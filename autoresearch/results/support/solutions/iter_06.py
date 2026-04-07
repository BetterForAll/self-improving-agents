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
                    
                    if "(most popular)" in value:
                        pricing_details["most_popular"] = True
                        value = value.replace("(most popular)", "").strip()
                    
                    if plan_name == "enterprise":
                        monthly_rate_match = re.search(r'(\$\d+)/month per seat', value, re.IGNORECASE)
                        if monthly_rate_match:
                            pricing_details["monthly_rate_per_seat"] = monthly_rate_match.group(1)
                        if "annual billing only" in value:
                            pricing_details["billing_type"] = "annual billing only"
                        
                    else:
                        monthly_match = re.search(r'(\$\d+)/month', value, re.IGNORECASE)
                        annual_match = re.search(r'(\$\d+)/year', value, re.IGNORECASE)
                        
                        if monthly_match:
                            pricing_details["monthly"] = monthly_match.group(1)
                        if annual_match:
                            pricing_details["annual"] = annual_match.group(1)
                        
                        if not monthly_match and not annual_match and not pricing_details.get("monthly_rate_per_seat") and value:
                            pricing_details["full_string"] = value
                    
                    parsed_kb[current_section][plan_name] = pricing_details

            elif current_section == "storage_limits":
                if ":" in item:
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
    
    def _detect_plans(q_lower, kb_plans):
        detected = []
        if re.search(r'\benterprise\b', q_lower):
            detected.append("enterprise")
        if re.search(r'\bpersonal\b', q_lower):
            detected.append("personal")
        
        # Detect "Pro" plan, careful not to confuse with "CloudSync Pro" product name
        if (re.search(r'\bpro plan\b', q_lower) or
            (re.search(r'\bpro\b(?!duct\b)', q_lower) and 
             not re.search(r'\bcloudsync pro\b', q_lower) and 
             any(k in q_lower for k in ["price", "cost", "storage", "capacity", "limit", "tier", "plan", "features", "what about", "how much", "how many", "amount"]))):
            if "pro" not in detected:
                detected.append("pro")
        
        return [p for p in list(dict.fromkeys(detected)) if p in kb_plans]

    all_kb_plans = set()
    if parsed_kb.get("pricing"):
        all_kb_plans.update(parsed_kb["pricing"].keys())
    if parsed_kb.get("storage_limits"):
        all_kb_plans.update(parsed_kb["storage_limits"].keys())
    
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

    if any(k in question_lower for k in ["price", "cost", "how much", "pricing", "monthly", "annual", "year", "month", "subscription", "tiers", "plans", "fee"]):
        intents["pricing"] = True
    if any(k in question_lower for k in ["storage", "capacity", "gb", "tb", "limit", "space", "data", "size", "how much space", "how many gb", "how many tb"]):
        intents["storage_limits"] = True
    if any(k in question_lower for k in ["trial", "free", "try out", "test", "evaluate", "demo", "sample", "days", "period"]):
        intents["free_trial"] = True
    if any(k in question_lower for k in ["platform", "device", "support", "os", "compatibility", "work on", "runs on", "mac", "windows", "linux", "ios", "android", "web"]):
        intents["supported_platforms"] = True
    if any(k in question_lower for k in ["feature", "what does it do", "abilities", "can it do", "functionality", "encryption", "sync", "real-time", "capabilities", "main features", "key functions"]):
        intents["key_features"] = True

    is_general_product_query_keywords = any(k in question_lower for k in ["what is cloudsync pro", "tell me about cloudsync pro", "about your service", "product description", "what is your product", "what is this service", "what is it"])
    
    has_other_specific_intent = any(v for k, v in intents.items() if k != "product_description") or requested_plans
    is_general_product_query_mention = re.search(r'\bcloudsync pro\b', question_lower) and not has_other_specific_intent

    if is_general_product_query_keywords or is_general_product_query_mention:
        intents["product_description"] = True
    
    is_comprehensive_query = intents["product_description"] and not has_other_specific_intent

    # --- Response Generation Helpers ---
    def _get_plan_pricing_string(plan_key, details, specific_pricing_type=None):
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
        else:
            if specific_pricing_type == "monthly" and details.get("monthly"):
                price_options.append(f"{details['monthly']}/month")
            elif specific_pricing_type == "annual" and details.get("annual"):
                price_options.append(f"{details['annual']}/year")
            elif details.get("monthly") and details.get("annual"):
                price_options.append(f"{details['monthly']}/month or {details['annual']}/year")
            elif details.get("monthly"):
                price_options.append(f"{details['monthly']}/month")
            elif details.get("annual"):
                price_options.append(f"{details['annual']}/year")
            elif details.get("full_string"):
                price_options.append(details['full_string'])
        
        if price_options:
            return f"{plan_prefix} costs {', or '.join(price_options)}."
        return None

    def _get_plan_storage_string(plan_key, storage_data):
        plan_display_name = plan_key.capitalize()
        if plan_key in storage_data:
            return f"The {plan_display_name} plan includes {storage_data[plan_key]} of storage."
        return None

    # Determine effective plans for listing details. Sort for consistent output.
    effective_plans = requested_plans if requested_plans and not is_comprehensive_query else sorted(list(all_kb_plans), key=lambda x: {'personal':0, 'pro':1, 'enterprise':2}.get(x,3))

    # --- Response Generation ---

    # Handle comprehensive product queries (e.g., "What is CloudSync Pro?")
    if is_comprehensive_query and parsed_kb.get("product_name"):
        response_parts.append(f"{parsed_kb['product_name']} is a {parsed_kb['product_description']}.")

        if parsed_kb.get("pricing"):
            pricing_summary = []
            for plan_key in effective_plans:
                if plan_key in parsed_kb["pricing"]:
                    plan_info = parsed_kb["pricing"][plan_key]
                    plan_display_name = plan_key.capitalize()
                    price_str_options = []
                    if plan_key == "enterprise":
                        if plan_info.get("monthly_rate_per_seat"):
                            enterprise_price_string = f"{plan_info['monthly_rate_per_seat']}/month per seat"
                            if plan_info.get("billing_type"):
                                enterprise_price_string += f", {plan_info['billing_type']}"
                            price_str_options.append(enterprise_price_string)
                    else:
                        if plan_info.get("monthly") and plan_info.get("annual"):
                            price_str_options.append(f"{plan_info['monthly']}/month or {plan_info['annual']}/year")
                        elif plan_info.get("monthly"):
                            price_str_options.append(f"{plan_info['monthly']}/month")
                        elif plan_info.get("annual"):
                            price_str_options.append(f"{plan_info['annual']}/year")
                    
                    if price_str_options:
                        prefix = ""
                        if plan_key == "pro" and plan_info.get("most_popular"):
                            prefix = "Our most popular "
                        pricing_summary.append(f"{prefix}{plan_display_name}: {', or '.join(price_str_options)}")
            if pricing_summary:
                response_parts.append("Pricing tiers are:")
                for summary_item in pricing_summary:
                    response_parts.append(f"- {summary_item}")

        if parsed_kb.get("storage_limits"):
            storage_summary = []
            for plan_key in effective_plans:
                if plan_key in parsed_kb["storage_limits"]:
                    plan_display_name = plan_key.capitalize()
                    storage_summary.append(f"{plan_display_name}: {parsed_kb['storage_limits'][plan_key]}")
            if storage_summary:
                response_parts.append("Storage limits are:")
                for summary_item in storage_summary:
                    response_parts.append(f"- {summary_item}")
        
        if parsed_kb.get("supported_platforms"):
            response_parts.append(f"It supports: {', '.join(parsed_kb['supported_platforms'])}.")

        if parsed_kb.get("key_features"):
            response_parts.append(f"Key features include: {', '.join(parsed_kb['key_features'])}.")

        if parsed_kb.get("free_trial"):
            response_parts.append(f"Additionally, {parsed_kb['free_trial']}.")
        
    else: # Handle specific queries
        if intents["product_description"] and parsed_kb.get("product_name") and parsed_kb.get("product_description"):
            response_parts.append(f"{parsed_kb['product_name']} is a {parsed_kb['product_description']}.")
            
        specific_pricing_requested_type = None
        if "monthly" in question_lower and "annual" not in question_lower:
            specific_pricing_requested_type = "monthly"
        elif "annual" in question_lower and "monthly" not in question_lower:
            specific_pricing_requested_type = "annual"
            
        if intents["pricing"] and parsed_kb.get("pricing"):
            plan_pricing_statements = []
            for plan_key in effective_plans:
                if plan_key in parsed_kb["pricing"]:
                    pricing_string = _get_plan_pricing_string(plan_key, parsed_kb["pricing"][plan_key], specific_pricing_requested_type)
                    if pricing_string:
                        plan_pricing_statements.append(pricing_string)
            
            if plan_pricing_statements:
                if len(plan_pricing_statements) == 1:
                    response_parts.append(plan_pricing_statements[0])
                else:
                    response_parts.append("Regarding pricing: " + " ".join(plan_pricing_statements))

        if intents["storage_limits"] and parsed_kb.get("storage_limits"):
            plan_storage_statements = []
            for plan_key in effective_plans:
                storage_string = _get_plan_storage_string(plan_key, parsed_kb["storage_limits"])
                if storage_string:
                    plan_storage_statements.append(storage_string)
            
            if plan_storage_statements:
                if len(plan_storage_statements) == 1:
                    response_parts.append(plan_storage_statements[0])
                else:
                    response_parts.append("Regarding storage: " + " ".join(plan_storage_statements))
                    
        if intents["free_trial"] and parsed_kb.get("free_trial"):
            response_parts.append(f"We offer a {parsed_kb['free_trial']}.")

        if intents["supported_platforms"] and parsed_kb.get("supported_platforms"):
            response_parts.append(f"CloudSync Pro supports: {', '.join(parsed_kb['supported_platforms'])}.")

        if intents["key_features"] and parsed_kb.get("key_features"):
            response_parts.append(f"Key features include: {', '.join(parsed_kb['key_features'])}.")

    # --- Construct final answer ---
    if response_parts:
        final_answer = " ".join(response_parts)
        if not final_answer.strip().endswith(('.', '!', '?')):
             final_answer += "."
        return final_answer + " Is there anything else I can help you with?"
    else:
        unfound_requested_plans = [p for p in requested_plans if p not in all_kb_plans]
        if unfound_requested_plans:
            return f"I couldn't find information for the {', '.join(p.capitalize() for p in unfound_requested_plans)} plan(s) in our knowledge base. We offer Personal, Pro, and Enterprise plans. Is there anything else I can help you with?"
        elif any(intents.values()): 
            return "I apologize, I couldn't find specific information to answer that question in our knowledge base. Please try rephrasing your question or ask about a different topic. Is there anything else I can help you with?"
        elif "cloudsync pro" in question_lower:
             return "I couldn't find a direct answer to your question about CloudSync Pro. Please try rephrasing your question or ask about specific features, pricing, or storage. Is there anything else I can help you with?"
        else:
            return "Thank you for contacting us. I couldn't find a direct answer to your question in our knowledge base. Please visit our website for more information or try rephrasing your question. Is there anything else I can help you with?"