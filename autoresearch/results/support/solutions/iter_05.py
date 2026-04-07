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
    def _detect_plans(q_lower, kb_plans):
        detected = []
        # Prioritize "Enterprise" and "Personal" as they are less ambiguous
        if re.search(r'\benterprise\b', q_lower):
            detected.append("enterprise")
        if re.search(r'\bpersonal\b', q_lower):
            detected.append("personal")
        
        # "Pro" plan detection. It's challenging because "pro" can be generic.
        # We'll assume "pro" refers to the plan if "pro plan" is explicit,
        # or if "pro" is used with specific plan-related keywords and not as part of the product name.
        if re.search(r'\bpro\s+plan\b', q_lower):
            if "pro" not in detected:
                detected.append("pro")
        elif (re.search(r'\bpro\b', q_lower) and
              not re.search(r'\bcloudsync pro\b', q_lower) and
              any(k in q_lower for k in ["price", "cost", "storage", "capacity", "limit", "tier", "how much"])):
            if "pro" not in detected:
                detected.append("pro")
        
        # Filter detected plans to only those existing in the KB
        return [p for p in list(dict.fromkeys(detected)) if p in kb_plans]

    # Collect all available plan names from KB for validation
    all_kb_plans = set()
    if parsed_kb.get("pricing"):
        all_kb_plans.update(parsed_kb["pricing"].keys())
    if parsed_kb.get("storage_limits"):
        all_kb_plans.update(parsed_kb["storage_limits"].keys())
    
    # Detect plans relevant to the question
    requested_plans = _detect_plans(question_lower, all_kb_plans)

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
    if any(k in question_lower for k in ["storage", "capacity", "gb", "tb", "limit", "space"]):
        intents["storage_limits"] = True
    if any(k in question_lower for k in ["trial", "free", "try out", "test"]):
        intents["free_trial"] = True
    if any(k in question_lower for k in ["platform", "device", "support", "os", "compatibility", "work on", "runs on", "mac", "windows", "linux", "ios", "android"]):
        intents["supported_platforms"] = True
    if any(k in question_lower for k in ["feature", "what does it do", "abilities", "can it do", "functionality", "encryption"]):
        intents["key_features"] = True

    # General product description intent (triggered by specific phrases or just product name without other intents)
    is_general_product_query_keywords = any(k in question_lower for k in ["what is cloudsync pro", "tell me about cloudsync pro", "about your service", "product description", "what is your product", "what is this service"])
    is_general_product_query_mention = re.search(r'\bcloudsync pro\b', question_lower) and not any(intents.values()) and not requested_plans

    if is_general_product_query_keywords or is_general_product_query_mention:
        intents["product_description"] = True
    
    # --- Response Generation ---

    # 1. Product Description (if it's a primary query or provides useful context)
    if intents["product_description"] and parsed_kb.get("product_name") and parsed_kb.get("product_description"):
        response_parts.append(f"{parsed_kb['product_name']} is a {parsed_kb['product_description']}.")
        
    # Determine target plans for details: If specific plans were requested, use them. Otherwise, list all plans from KB.
    # Sort for consistent output if listing all
    effective_plans_for_details = sorted(list(requested_plans)) if requested_plans else sorted(list(all_kb_plans), key=lambda x: {"personal":0, "pro":1, "enterprise":2}.get(x,3))
    
    # Helper to generate pricing statement for a single plan
    def _get_pricing_statement(plan_key, details, specific_type=None):
        plan_display_name = plan_key.capitalize()
        plan_prefix = ""
        if plan_key == "pro" and details.get("most_popular"):
            plan_prefix = f"Our most popular {plan_display_name}"
        else:
            plan_prefix = f"The {plan_display_name}"

        price_options = []
        if plan_key == "enterprise":
            if details.get("monthly_rate_per_seat"):
                enterprise_price_string = f"{details['monthly_rate_per_seat']}/month per seat"
                if details.get("billing_type"):
                    enterprise_price_string += f", {details['billing_type']}"
                price_options.append(enterprise_price_string)
        else: # Personal and Pro plans
            if specific_type == "monthly" and details.get("monthly"):
                price_options.append(f"{details['monthly']}/month")
            elif specific_type == "annual" and details.get("annual"):
                price_options.append(f"{details['annual']}/year")
            elif details.get("monthly") and details.get("annual"): # Both available, no specific type requested
                price_options.append(f"{details['monthly']}/month or {details['annual']}/year")
            elif details.get("monthly"): # Only monthly available
                price_options.append(f"{details['monthly']}/month")
            elif details.get("annual"): # Only annual available
                price_options.append(f"{details['annual']}/year")
            elif details.get("full_string"): # Fallback for unparsed formats
                price_options.append(details['full_string'])
        
        if price_options:
            return f"{plan_prefix} plan costs {', or '.join(price_options)}."
        return ""

    if intents["pricing"] and parsed_kb.get("pricing"):
        specific_pricing_requested_type = None
        if "monthly" in question_lower and "annual" not in question_lower:
            specific_pricing_requested_type = "monthly"
        elif "annual" in question_lower and "monthly" not in question_lower:
            specific_pricing_requested_type = "annual"
            
        if not requested_plans and len(all_kb_plans) > 1: # General pricing query, summarize all plans
            summary_parts = []
            for plan_key in effective_plans_for_details: 
                if plan_key in parsed_kb["pricing"]:
                    details = parsed_kb["pricing"][plan_key]
                    plan_display_name = plan_key.capitalize()
                    
                    price_info = []
                    if plan_key == "enterprise":
                        if details.get("monthly_rate_per_seat"):
                            price_str = f"{details['monthly_rate_per_seat']}/month per seat"
                            if details.get("billing_type"):
                                price_str += f" ({details['billing_type']})"
                            price_info.append(price_str)
                    else:
                        if details.get("monthly"):
                            price_info.append(f"{details['monthly']}/month")
                        if details.get("annual"):
                            price_info.append(f"{details['annual']}/year")
                    
                    if price_info:
                        plan_descriptor = plan_display_name
                        if plan_key == "pro" and details.get("most_popular"):
                            plan_descriptor = f"{plan_display_name} (most popular)"
                        summary_parts.append(f"{plan_descriptor}: {', '.join(price_info)}")
            
            if summary_parts:
                response_parts.append(f"CloudSync Pro offers the following pricing plans: {'; '.join(summary_parts)}.")
        else: # Specific plans requested or only one plan is relevant
            plan_pricing_statements = []
            for plan_key in effective_plans_for_details:
                if plan_key in parsed_kb["pricing"]:
                    statement = _get_pricing_statement(plan_key, parsed_kb["pricing"][plan_key], specific_pricing_requested_type)
                    if statement:
                        plan_pricing_statements.append(statement)
            if plan_pricing_statements:
                response_parts.append(" ".join(plan_pricing_statements))

    if intents["storage_limits"] and parsed_kb.get("storage_limits"):
        if not requested_plans and len(all_kb_plans) > 1: # General storage query, summarize all plans
            summary_parts = []
            for plan_key in effective_plans_for_details:
                if plan_key in parsed_kb["storage_limits"]:
                    plan_display_name = plan_key.capitalize()
                    summary_parts.append(f"{plan_display_name}: {parsed_kb['storage_limits'][plan_key]}")
            if summary_parts:
                response_parts.append(f"Storage limits for CloudSync Pro plans are: {'; '.join(summary_parts)}.")
        else: # Specific plans requested or only one plan is relevant
            plan_storage_statements = []
            for plan_key in effective_plans_for_details:
                if plan_key in parsed_kb["storage_limits"]:
                    plan_display_name = plan_key.capitalize()
                    plan_storage_statements.append(f"The {plan_display_name} plan includes {parsed_kb['storage_limits'][plan_key]} of storage.")
            if plan_storage_statements:
                response_parts.append(" ".join(plan_storage_statements))
            
    # 3. General Information (Free Trial, Platforms, Features)
    # These are added if explicitly requested, regardless of plan context, as they apply to the service generally.
    
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
        product_name = parsed_kb.get("product_name", "CloudSync Pro")
        
        if requested_plans: # Plans were mentioned, but no specific information for them could be found based on other keywords
            unfound_requested_plans = [p for p in requested_plans if p not in all_kb_plans]
            if unfound_requested_plans:
                return f"I couldn't find information for the {', '.join(p.capitalize() for p in unfound_requested_plans)} plan(s) in our knowledge base. {product_name} offers Personal, Pro, and Enterprise plans. Is there anything else I can help you with?"
            else: # Plans were found, but no relevant intent was triggered by other keywords
                return f"I apologize, I couldn't find specific information to answer that question about the requested plan(s) in our knowledge base. Please try rephrasing your question or ask about a different topic. Is there anything else I can help you with?"
        elif any(intents.values()): # Intent was detected, but no data found (e.g., asking for "security features" when KB only lists "encryption")
            return f"I apologize, I couldn't find specific information to answer that question in our knowledge base. Please try rephrasing your question or ask about a different topic. Is there anything else I can help you with?"
        elif "cloudsync pro" in question_lower or len(question_lower.split()) < 5: # General query mentioning product or very short query
            info_options = []
            if parsed_kb.get("product_name") and parsed_kb.get("product_description"): info_options.append("what the service is")
            if parsed_kb.get("pricing"): info_options.append("pricing details")
            if parsed_kb.get("storage_limits"): info_options.append("storage limits")
            if parsed_kb.get("free_trial"): info_options.append("free trial information")
            if parsed_kb.get("supported_platforms"): info_options.append("supported platforms")
            if parsed_kb.get("key_features"): info_options.append("key features")
            
            if info_options:
                return f"I couldn't find a direct answer to your question about {product_name}. I can tell you about {', '.join(info_options)}. Is there anything specific you'd like to know?"
            else: # KB is empty or too minimal for general info
                 return f"I couldn't find a direct answer to your question about {product_name}. Please try rephrasing your question. Is there anything else I can help you with?"
        else: # Completely unrecognized or irrelevant question
            return "Thank you for contacting us. I couldn't find a direct answer to your question in our knowledge base. Please visit our website for more information or try rephrasing your question. Is there anything else I can help you with?"