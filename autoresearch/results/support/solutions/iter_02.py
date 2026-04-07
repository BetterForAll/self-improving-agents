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
            parsed_kb["free_trial"] = line.split(":", 1)[1].strip()
            current_section = None
        elif line.startswith("Supported Platforms:"):
            parsed_kb["supported_platforms"] = line.split(":", 1)[1].strip()
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
    # Use a list to track found info types, allowing for multiple types in one response
    info_found_in_sections = [] 

    # Identify requested plans
    requested_plans = []
    
    # Prioritize Enterprise/Personal as they are less ambiguous than "Pro"
    if re.search(r'\benterprise\b', question_lower):
        requested_plans.append("enterprise")
    if re.search(r'\bpersonal\b', question_lower):
        requested_plans.append("personal")
    
    # "Pro" plan detection is tricky because "CloudSync Pro" is the product name.
    # Look for "pro plan" or "pro" in specific contexts related to features, pricing, storage, etc.
    # Exclude cases where "pro" is part of "CloudSync Pro" unless explicitly asking about the "Pro plan"
    if (re.search(r'\bpro plan\b', question_lower) or
        (re.search(r'\bpro\b(?!duct)', question_lower) and # 'pro' not immediately followed by 'duct'
         not re.search(r'\bcloudsync pro\b', question_lower) and # Ensure it's not just product name
         any(k in question_lower for k in ["price", "cost", "storage", "capacity", "limit", "plan", "features", "what about pro"]))):
        if "pro" not in requested_plans:
            requested_plans.append("pro")
            
    # Remove duplicates and preserve order
    requested_plans = list(dict.fromkeys(requested_plans))


    # --- General product description ---
    # Trigger if question is about the product itself, or if "CloudSync Pro" is mentioned
    # without specific keywords for pricing/storage/features etc., and no other specific info has been added yet.
    is_general_product_query = (
        any(k in question_lower for k in ["what is cloudsync pro", "tell me about cloudsync pro", "about your service", "product description", "what is your product"]) or
        (re.search(r'\bcloudsync pro\b', question_lower) and
         not any(k in question_lower for k in ["price", "cost", "storage", "feature", "trial", "platform", "plan", "limit", "gb", "tb", "month", "year", "how much"]))
    )
    
    if is_general_product_query and not response_parts: # Only provide general description if nothing more specific has been found
        if parsed_kb.get("product_name") and parsed_kb.get("product_description"):
            response_parts.append(f"{parsed_kb['product_name']} is a {parsed_kb['product_description']}.")
            info_found_in_sections.append("product_description")


    # --- Pricing Information ---
    pricing_keywords = ["price", "cost", "how much", "pricing"]
    is_pricing_query = any(k in question_lower for k in pricing_keywords)
    if is_pricing_query:
        pricing_info = parsed_kb.get("pricing")
        if pricing_info:
            # If no specific plans requested, default to listing all plans
            target_plans = requested_plans if requested_plans else list(pricing_info.keys())
            
            specific_pricing_requested_type = None
            if "monthly" in question_lower and "annual" not in question_lower:
                specific_pricing_requested_type = "monthly"
            elif "annual" in question_lower and "monthly" not in question_lower:
                specific_pricing_requested_type = "annual"
            
            plan_price_statements = []
            for plan_key in target_plans:
                if plan_key in pricing_info:
                    details = pricing_info[plan_key]
                    plan_display_name = plan_key.capitalize()
                    
                    plan_prefix = ""
                    if plan_key == "pro" and details.get("most_popular"):
                        plan_prefix = f"Our most popular {plan_display_name} plan"
                    else:
                        plan_prefix = f"The {plan_display_name} plan"

                    price_parts = []
                    if plan_key == "enterprise":
                        if details.get("monthly_rate_per_seat"):
                            enterprise_price_string = f"{details['monthly_rate_per_seat']}/month per seat"
                            if details.get("billing_type"):
                                enterprise_price_string += f", {details['billing_type']}"
                            price_parts.append(enterprise_price_string)
                    else: # Personal and Pro plans
                        if specific_pricing_requested_type == "monthly" and details.get("monthly"):
                            price_parts.append(f"{details['monthly']}/month")
                        elif specific_pricing_requested_type == "annual" and details.get("annual"):
                            price_parts.append(f"{details['annual']}/year")
                        elif details.get("monthly") and details.get("annual"):
                            price_parts.append(f"{details['monthly']}/month or {details['annual']}/year")
                        elif details.get("monthly"):
                            price_parts.append(f"{details['monthly']}/month")
                        elif details.get("annual"):
                            price_parts.append(f"{details['annual']}/year")
                        elif details.get("full_string"): # Fallback for unexpected formats
                            price_parts.append(details['full_string'])
                    
                    if price_parts:
                        plan_price_statements.append(f"{plan_prefix} costs {', or '.join(price_parts)}.")
            
            if plan_price_statements:
                response_parts.append(" ".join(plan_price_statements))
                info_found_in_sections.append("pricing")

    # --- Storage Limits ---
    storage_keywords = ["storage", "capacity", "gb", "tb", "limit"]
    is_storage_query = any(k in question_lower for k in storage_keywords)
    if is_storage_query:
        storage_info = parsed_kb.get("storage_limits")
        if storage_info:
            # If no specific plans requested, default to listing all plans
            target_plans = requested_plans if requested_plans else list(storage_info.keys())
            
            plan_storage_statements = []
            for plan_key in target_plans:
                if plan_key in storage_info:
                    plan_display_name = plan_key.capitalize()
                    plan_storage_statements.append(f"The {plan_display_name} plan includes {storage_info[plan_key]} of storage.")
            
            if plan_storage_statements:
                response_parts.append(" ".join(plan_storage_statements))
                info_found_in_sections.append("storage_limits")

    # --- Free Trial ---
    if any(k in question_lower for k in ["trial", "free"]):
        free_trial_info = parsed_kb.get("free_trial")
        if free_trial_info:
            response_parts.append(f"We offer a {free_trial_info}.")
            info_found_in_sections.append("free_trial")

    # --- Supported Platforms ---
    if any(k in question_lower for k in ["platform", "device", "support", "os", "compatibility", "work on", "runs on"]):
        platforms_info = parsed_kb.get("supported_platforms")
        if platforms_info:
            response_parts.append(f"CloudSync Pro supports: {platforms_info}.")
            info_found_in_sections.append("supported_platforms")

    # --- Key Features ---
    if any(k in question_lower for k in ["feature", "what does it do", "abilities", "can it do"]):
        features_info = parsed_kb.get("key_features")
        if features_info:
            response_parts.append(f"Key features include: {', '.join(features_info)}.")
            info_found_in_sections.append("key_features")

    # --- Construct final answer ---
    if response_parts:
        final_answer = " ".join(response_parts)
        # Ensure proper punctuation at the end of the sentence before adding the closing phrase
        if not final_answer.strip().endswith(('.', '!', '?')):
             final_answer += "."
        return final_answer + " Is there anything else I can help you with?"
    else:
        # Provide a more specific fallback if a general product query was made but failed
        if is_general_product_query and "product_description" not in info_found_in_sections:
            return "Thank you for contacting us. I couldn't find a direct answer to your question about CloudSync Pro. Please visit our website for more information or try rephrasing your question."
        else:
            return "Thank you for contacting us. I couldn't find a direct answer to your question in our knowledge base. Please visit our website for more information or try rephrasing your question."