import re

def _parse_knowledge_base(kb_string):
    """Parses the knowledge base string into a structured dictionary."""
    parsed_kb = {}
    lines = kb_string.strip().split('\n')
    current_section = None

    # Helper to clean plan names for dictionary keys
    def clean_plan_name(name):
        return name.lower().replace(':', '').strip()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("Product:"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                product_info = parts[1].strip().split(" -- ", 1)
                parsed_kb["product_name"] = product_info[0].strip()
                parsed_kb["product_description"] = product_info[1].strip() if len(product_info) > 1 else ""
            current_section = None
        elif line.startswith("Pricing:"):
            current_section = "pricing"
            parsed_kb[current_section] = {}
        elif line.startswith("Storage Limits:"):
            current_section = "storage_limits"
            parsed_kb[current_section] = {}
        elif line.startswith("Free Trial:"):
            # Store the full string for the trial description
            parsed_kb["free_trial"] = line.split(":", 1)[1].strip()
            current_section = None
        elif line.startswith("Supported Platforms:"):
            # Store as a list for easier iteration/joining
            platforms_str = line.split(":", 1)[1].strip()
            parsed_kb["supported_platforms"] = [p.strip() for p in platforms_str.split(',')]
            current_section = None
        elif line.startswith("Key Features:"):
            current_section = "key_features"
            parsed_kb[current_section] = []
        elif line.startswith("- ") and current_section:
            item = line[2:].strip()
            if current_section == "pricing":
                if ":" in item:
                    plan_name_raw, value = item.split(":", 1)
                    plan_name = clean_plan_name(plan_name_raw)
                    
                    pricing_details = {}
                    value = value.strip()
                    
                    # Check for "most popular" tag
                    if "(most popular)" in value:
                        pricing_details["most_popular"] = True
                        value = value.replace("(most popular)", "").strip()
                    
                    # Specific handling for Enterprise pricing format
                    if plan_name == "enterprise":
                        monthly_rate_match = re.search(r'(\$\d+)/month per seat', value, re.IGNORECASE)
                        if monthly_rate_match:
                            pricing_details["monthly_rate_per_seat"] = monthly_rate_match.group(1)
                        if "annual billing only" in value:
                            pricing_details["billing_type"] = "annual billing only"
                        
                    else: # Personal and Pro plans
                        monthly_match = re.search(r'(\$\d+)/month', value, re.IGNORECASE)
                        annual_match = re.search(r'(\$\d+)/year', value, re.IGNORECASE)
                        
                        if monthly_match:
                            pricing_details["monthly"] = monthly_match.group(1)
                        if annual_match:
                            pricing_details["annual"] = annual_match.group(1)
                        
                        # Fallback for unexpected formats, store full string if no specific price parsed
                        if not monthly_match and not annual_match and not pricing_details.get("monthly_rate_per_seat") and value:
                            pricing_details["full_string"] = value
                    
                    parsed_kb[current_section][plan_name] = pricing_details

            elif current_section == "storage_limits":
                if ":" in item: # Ensure it's a key-value pair
                    plan_name, value = item.split(":", 1)
                    parsed_kb[current_section][clean_plan_name(plan_name)] = value.strip()
            elif current_section == "key_features":
                parsed_kb[current_section].append(item)
    return parsed_kb


def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    parsed_kb = _parse_knowledge_base(knowledge_base)
    question_lower = question.lower()
    response_parts = []
    
    # Helper to detect plans mentioned in the question
    def _detect_plans(q_lower, kb_plans_set):
        detected = []
        # Prioritize "Enterprise" and "Personal" as they are less ambiguous
        if re.search(r'\benterprise\b', q_lower):
            detected.append("enterprise")
        if re.search(r'\bpersonal\b', q_lower):
            detected.append("personal")
        
        # "Pro" plan detection. More specific context required.
        # Look for "pro plan", or "pro" followed by keywords like 'price', 'storage', 'feature', 'limit', 'cost', 'capacity', 'tier', 'version'.
        # Also exclude "CloudSync Pro" if it's just referring to the product name.
        if (re.search(r'\bpro plan\b', q_lower) or
            (re.search(r'\bpro\b(?!duct\b| version\b)', q_lower) and # 'pro' not immediately followed by 'product' or 'version'
             not re.search(r'\bcloudsync pro\b', q_lower) and # Ensure it's not just product name
             any(k in q_lower for k in ["price", "cost", "storage", "capacity", "limit", "tier", "plan", "features", "what about", "how much", "how many", "size"]))):
            if "pro" not in detected:
                detected.append("pro")
        
        # Filter detected plans to only those existing in the KB and maintain order
        return [p for p in list(dict.fromkeys(detected)) if p in kb_plans_set]

    # Collect all available plan names from KB for validation
    all_kb_plans_set = set()
    if parsed_kb.get("pricing"):
        all_kb_plans_set.update(parsed_kb["pricing"].keys())
    if parsed_kb.get("storage_limits"):
        all_kb_plans_set.update(parsed_kb["storage_limits"].keys())
    
    # Detect plans relevant to the question
    requested_plans = _detect_plans(question_lower, all_kb_plans_set)

    # --- Intent Detection ---
    intents = {
        "product_description": False,
        "pricing": False,
        "storage_limits": False,
        "free_trial": False,
        "supported_platforms": False,
        "key_features": False,
    }

    # Set intent flags based on keywords
    if any(k in question_lower for k in ["price", "cost", "how much", "pricing", "monthly", "annual", "year", "month"]):
        intents["pricing"] = True
    if any(k in question_lower for k in ["storage", "capacity", "gb", "tb", "limit", "space", "how many"]):
        intents["storage_limits"] = True
    if any(k in question_lower for k in ["trial", "free", "try out", "test", "demo"]):
        intents["free_trial"] = True
    if any(k in question_lower for k in ["platform", "device", "support", "os", "compatibility", "work on", "runs on", "mac", "windows", "linux", "ios", "android", "browser"]):
        intents["supported_platforms"] = True
    if any(k in question_lower for k in ["feature", "what does it do", "abilities", "can it do", "functionality", "encryption", "what are", "benefits"]):
        intents["key_features"] = True

    # General product description intent (triggered by specific phrases or just product name without other intents)
    is_general_product_query_keywords = any(k in question_lower for k in ["what is cloudsync pro", "tell me about cloudsync pro", "about your service", "product description", "what is your product", "what is this service", "what is it"])
    # Trigger if CloudSync Pro is mentioned AND no other strong intent or specific plan is requested.
    is_general_product_query_mention = re.search(r'\bcloudsync pro\b', question_lower) and not any(v for k, v in intents.items() if k != "product_description") and not requested_plans

    if is_general_product_query_keywords or is_general_product_query_mention:
        intents["product_description"] = True
    
    # --- Response Generation ---

    # 1. Product Description (if it's a primary query or provides useful context)
    if intents["product_description"] and parsed_kb.get("product_name") and parsed_kb.get("product_description"):
        response_parts.append(f"{parsed_kb['product_name']} is a {parsed_kb['product_description']}.")
        
    # Determine if a general summary is needed for pricing/storage (i.e., no specific plan requested)
    needs_general_pricing_summary = intents["pricing"] and not requested_plans
    needs_general_storage_summary = intents["storage_limits"] and not requested_plans
    
    # List of plans for which we have data and can potentially provide details (for summaries or specific requests)
    # Sort plans for consistent output order
    available_plans_sorted = sorted(list(all_kb_plans_set), key=lambda x: ['personal', 'pro', 'enterprise'].index(x) if x in ['personal', 'pro', 'enterprise'] else 99)

    # 2. Pricing Information
    if intents["pricing"] and parsed_kb.get("pricing"):
        if needs_general_pricing_summary:
            summary_parts = []
            min_price_monthly = float('inf')
            max_price_monthly_per_seat = 0
            pro_price_monthly = None

            for plan_key in available_plans_sorted:
                details = parsed_kb["pricing"].get(plan_key)
                if details:
                    if plan_key == "personal" and details.get("monthly"):
                        min_price_monthly = min(min_price_monthly, float(details["monthly"].replace('$', '')))
                    if plan_key == "pro" and details.get("monthly"):
                        pro_price_monthly = details["monthly"]
                    if plan_key == "enterprise" and details.get("monthly_rate_per_seat"):
                        max_price_monthly_per_seat = max(max_price_monthly_per_seat, float(details["monthly_rate_per_seat"].replace('$', '')))
            
            if min_price_monthly != float('inf') or pro_price_monthly or max_price_monthly_per_seat > 0:
                price_summary_str = "CloudSync Pro offers various plans."
                if min_price_monthly != float('inf'):
                    price_summary_str += f" The Personal plan starts at ${int(min_price_monthly)}/month."
                if pro_price_monthly:
                    price_summary_str += f" Our most popular Pro plan is {pro_price_monthly}/month."
                if max_price_monthly_per_seat > 0:
                    price_summary_str += f" The Enterprise plan is ${int(max_price_monthly_per_seat)}/month per seat with annual billing only."
                price_summary_str += " Annual billing options are available for Personal and Pro plans offering a discount."
                
                summary_parts.append(price_summary_str)
            
            if summary_parts:
                response_parts.append(" ".join(summary_parts).strip())

        # Specific pricing details for requested plans (if any were specifically mentioned)
        if requested_plans:
            plan_pricing_statements = []
            specific_pricing_requested_type = None # To distinguish 'monthly' vs 'annual' queries
            if "monthly" in question_lower and "annual" not in question_lower:
                specific_pricing_requested_type = "monthly"
            elif "annual" in question_lower and "monthly" not in question_lower:
                specific_pricing_requested_type = "annual"
                
            for plan_key in requested_plans:
                if plan_key in parsed_kb["pricing"]:
                    details = parsed_kb["pricing"][plan_key]
                    plan_display_name = plan_key.capitalize()
                    
                    plan_prefix = ""
                    if plan_key == "pro" and details.get("most_popular"):
                        plan_prefix = f"Our most popular {plan_display_name} plan"
                    else:
                        plan_prefix = f"The {plan_display_name} plan"

                    price_options = []
                    if plan_key == "enterprise":
                        if details.get("monthly_rate_per_seat"):
                            enterprise_price_string = f"{details['monthly_rate_per_seat']}/month per seat"
                            if details.get("billing_type"):
                                enterprise_price_string += f", {details['billing_type']}"
                            price_options.append(enterprise_price_string)
                    else: # Personal and Pro plans
                        if specific_pricing_requested_type == "monthly" and details.get("monthly"):
                            price_options.append(f"{details['monthly']}/month")
                        elif specific_pricing_requested_type == "annual" and details.get("annual"):
                            price_options.append(f"{details['annual']}/year")
                        elif details.get("monthly") and details.get("annual"):
                            price_options.append(f"{details['monthly']}/month or {details['annual']}/year")
                        elif details.get("monthly"):
                            price_options.append(f"{details['monthly']}/month")
                        elif details.get("annual"):
                            price_options.append(f"{details['annual']}/year")
                        elif details.get("full_string"): # Fallback for unparsed formats
                            price_options.append(details['full_string'])
                    
                    if price_options:
                        plan_pricing_statements.append(f"{plan_prefix} costs {', or '.join(price_options)}.")
            
            if plan_pricing_statements:
                response_parts.append(" ".join(plan_pricing_statements))

    # 3. Storage Information
    if intents["storage_limits"] and parsed_kb.get("storage_limits"):
        # Helper to parse storage values into GB for comparison
        def parse_storage_to_gb(s):
            match = re.match(r'(\d+)(GB|TB)', s, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                unit = match.group(2).upper()
                if unit == 'TB':
                    return value * 1024 # Convert TB to GB for comparison
                return value
            return 0 # Default if unparseable

        if needs_general_storage_summary:
            summary_parts = []
            storage_values_processed = [] # (gb_value, original_string, plan_key)

            for plan_key in available_plans_sorted:
                storage_str = parsed_kb["storage_limits"].get(plan_key)
                if storage_str:
                    storage_gb = parse_storage_to_gb(storage_str)
                    if storage_gb > 0:
                        storage_values_processed.append((storage_gb, storage_str, plan_key))

            if storage_values_processed:
                min_storage_info = min(storage_values_processed, key=lambda x: x[0])
                max_storage_info = max(storage_values_processed, key=lambda x: x[0])
                
                storage_summary_str = f"CloudSync Pro plans offer storage ranging from {min_storage_info[1]} for the {min_storage_info[2].capitalize()} plan"
                if min_storage_info[0] != max_storage_info[0]: # If there's actually a range
                     storage_summary_str += f" up to {max_storage_info[1]} per seat for the {max_storage_info[2].capitalize()} plan."
                else: # Only one type of storage if min and max are the same
                    storage_summary_str += "." 
                summary_parts.append(storage_summary_str)
            
            if summary_parts:
                response_parts.append(" ".join(summary_parts))
        
        # Specific storage details for requested plans (if any were specifically mentioned)
        if requested_plans:
            plan_storage_statements = []
            for plan_key in requested_plans:
                if plan_key in parsed_kb["storage_limits"]:
                    plan_display_name = plan_key.capitalize()
                    plan_storage_statements.append(f"The {plan_display_name} plan includes {parsed_kb['storage_limits'][plan_key]} of storage.")
            
            if plan_storage_statements:
                response_parts.append(" ".join(plan_storage_statements))
            
    # 4. General Information (Free Trial, Platforms, Features)
    
    if intents["free_trial"] and parsed_kb.get("free_trial"):
        response_parts.append(f"We offer a {parsed_kb['free_trial']}.")

    if intents["supported_platforms"] and parsed_kb.get("supported_platforms"):
        response_parts.append(f"CloudSync Pro supports: {', '.join(parsed_kb['supported_platforms'])}.")

    if intents["key_features"] and parsed_kb.get("key_features"):
        response_parts.append(f"Key features include: {', '.join(parsed_kb['key_features'])}.")

    # --- Construct final answer ---
    if response_parts:
        final_answer = " ".join(response_parts)
        # Ensure proper punctuation at the end of the sentence before adding the closing phrase
        if not final_answer.strip().endswith(('.', '!', '?')):
             final_answer += "."
        return final_answer + " Is there anything else I can help you with?"
    else:
        # Fallback messages based on whether an intent was recognized or CloudSync Pro was mentioned
        if any(intents.values()): 
            # If an intent was detected but no information was found (e.g., asking for non-existent plan details)
            available_info_types = []
            if parsed_kb.get("pricing"): available_info_types.append("pricing")
            if parsed_kb.get("storage_limits"): available_info_types.append("storage limits")
            if parsed_kb.get("free_trial"): available_info_types.append("free trial")
            if parsed_kb.get("supported_platforms"): available_info_types.append("supported platforms")
            if parsed_kb.get("key_features"): available_info_types.append("key features")

            # Check if requested plans were not found
            if requested_plans:
                unfound_requested_plans = [p for p in requested_plans if p not in all_kb_plans_set]
                if unfound_requested_plans:
                    return f"I couldn't find information for the {', '.join(p.capitalize() for p in unfound_requested_plans)} plan(s) in our knowledge base. We offer Personal, Pro, and Enterprise plans. Is there anything else I can help you with?"
            
            # If no specific plan issue, but general intent not fulfilled
            if available_info_types:
                return f"I apologize, I couldn't find specific information to answer that question. I can provide information on {', '.join(available_info_types)}. Please try rephrasing your question or ask about one of these topics. Is there anything else I can help you with?"
            else:
                return "I apologize, I couldn't find specific information to answer that question in our knowledge base. Please try rephrasing your question or ask about a different topic. Is there anything else I can help you with?"
        
        elif "cloudsync pro" in question_lower:
             return "I couldn't find a direct answer to your question about CloudSync Pro. Please try rephrasing your question or ask about specific features, pricing, or storage. Is there anything else I can help you with?"
        else:
            return "Thank you for contacting us. I couldn't find a direct answer to your question in our knowledge base. Please visit our website for more information or try rephrasing your question. Is there anything else I can help you with?"