def answer_question(question, knowledge_base):
    import re

    # --- Knowledge Base Parsing ---
    parsed_kb = {}

    # Default product name and description
    product_name = "CloudSync Pro"
    product_description = "Cloud File Synchronization Service"

    product_match = re.search(r"Product: (.+?) -- (.+)", knowledge_base)
    if product_match:
        product_name = product_match.group(1).strip()
        product_description = product_match.group(2).strip()
    parsed_kb['product_name'] = product_name
    parsed_kb['product_description'] = product_description

    # Pricing (stores details and flags like 'popular', 'annual_billing_only')
    pricing_data = {}
    pricing_match = re.search(r"Pricing:\n((?:  - .+\n)+)", knowledge_base)
    if pricing_match:
        for line in pricing_match.group(1).strip().split('\n'):
            plan_match = re.match(r"  - (\w+): (.+)", line)
            if plan_match:
                plan_name = plan_match.group(1).lower()
                details = plan_match.group(2).strip()
                pricing_info = {'details': details}
                if '(most popular)' in details.lower():
                    pricing_info['popular'] = True
                if 'annual billing only' in details.lower():
                    pricing_info['annual_billing_only'] = True
                pricing_data[plan_name] = pricing_info
    parsed_kb['pricing'] = pricing_data # Ensure it's always present, even if empty

    # Storage Limits
    storage_data = {}
    storage_match = re.search(r"Storage Limits:\n((?:  - .+\n)+)", knowledge_base)
    if storage_match:
        for line in storage_match.group(1).strip().split('\n'):
            plan_match = re.match(r"  - (\w+): (.+)", line)
            if plan_match:
                storage_data[plan_match.group(1).lower()] = plan_match.group(2).strip()
    parsed_kb['storage_limits'] = storage_data # Ensure it's always present

    # Free Trial
    free_trial_match = re.search(r"Free Trial: (.+)", knowledge_base)
    parsed_kb['free_trial'] = free_trial_match.group(1).strip() if free_trial_match else None

    # Supported Platforms
    platforms_match = re.search(r"Supported Platforms: (.+)", knowledge_base)
    parsed_kb['supported_platforms'] = [p.strip() for p in platforms_match.group(1).split(',')] if platforms_match else []

    # Key Features
    features_list = []
    features_match = re.search(r"Key Features:\n((?:  - .+\n)+)", knowledge_base)
    if features_match:
        for line in features_match.group(1).strip().split('\n'):
            feature_match = re.match(r"  - (.+)", line)
            if feature_match:
                features_list.append(feature_match.group(1).strip())
    parsed_kb['key_features'] = features_list # Ensure it's always present

    # --- Intent Detection ---
    question_lower = question.lower()
    
    intents = {
        'request_free_trial': False,
        'request_popular_plan': False,
        'request_pricing': False,
        'request_storage': False,
        'request_platforms': False,
        'request_features': False,
        'request_product_description': False,
        'plans_mentioned': set(), # Specific plans mentioned in the question
        'general_pricing_query': False, # User asked for pricing, but not for a specific plan
        'general_storage_query': False # User asked for storage, but not for a specific plan
    }

    # Helper to find plan names robustly using word boundaries
    all_plan_names = sorted(list(parsed_kb['pricing'].keys()), key=len, reverse=True) # Check longer names first
    if all_plan_names:
        plan_name_pattern = r'\b(' + '|'.join(re.escape(p) for p in all_plan_names) + r')\b'
        found_plans = re.findall(plan_name_pattern, question_lower)
        intents['plans_mentioned'].update(found_plans)

    # Detect primary intents
    if any(keyword in question_lower for keyword in ["trial", "free", "demo", "test", "try"]):
        intents['request_free_trial'] = True

    if "most popular" in question_lower:
        intents['request_popular_plan'] = True
    
    pricing_keywords = ["price", "cost", "how much", "monthly", "annual", "subscription", "pricing"]
    if any(keyword in question_lower for keyword in pricing_keywords):
        intents['request_pricing'] = True
        if not intents['plans_mentioned']:
            intents['general_pricing_query'] = True

    storage_keywords = ["storage", "gb", "tb", "space", "limit", "capacity"]
    if any(keyword in question_lower for keyword in storage_keywords):
        intents['request_storage'] = True
        if not intents['plans_mentioned']:
            intents['general_storage_query'] = True

    if any(keyword in question_lower for keyword in ["platform", "device", "os", "compatible", "support", "work on", "run on", "app"]):
        intents['request_platforms'] = True

    if any(keyword in question_lower for keyword in ["feature", "what does it do", "can it", "encryption", "sync", "capabilities", "real-time", "end-to-end"]):
        intents['request_features'] = True

    # Product Description: As a fallback if no other strong specific intent is detected
    if not any(intents[key] for key in ['request_free_trial', 'request_popular_plan', 'request_pricing', 
                                        'request_storage', 'request_platforms', 'request_features']) \
       and not intents['plans_mentioned']:
        if product_name.lower() in question_lower or "what is" in question_lower or "tell me about" in question_lower:
             intents['request_product_description'] = True

    # --- Constructing the Answer based on Detected Intents ---
    response_parts = []
    
    # 1. Handle Free Trial
    if intents['request_free_trial']:
        if parsed_kb['free_trial']:
            response_parts.append(f"Yes, {product_name} offers a {parsed_kb['free_trial']}.")
        else:
            response_parts.append(f"I don't have information about a free trial for {product_name}.")

    # 2. Handle Most Popular Plan (if requested, and not already covered as part of a detailed plan statement)
    # This ensures "most popular" is mentioned early if it's a primary query.
    if intents['request_popular_plan'] and not any("most popular" in part.lower() for part in response_parts):
        popular_plan_name = None
        for plan_name, plan_info in parsed_kb['pricing'].items():
            if plan_info.get('popular'):
                popular_plan_name = plan_name
                price_text = plan_info['details'].replace('(most popular)', '').strip()
                response_parts.append(f"The {plan_name.capitalize()} plan is the most popular, costing {price_text}.")
                break
        if not popular_plan_name:
             response_parts.append(f"I don't have information on which plan is most popular for {product_name}.")

    # 3. Handle specific plans (combine pricing, storage, or general info about each mentioned plan)
    plans_to_detail = sorted(list(intents['plans_mentioned']))
    
    for plan in plans_to_detail:
        plan_description_parts = []
        
        # Determine if this plan is popular
        is_popular_plan = parsed_kb['pricing'].get(plan, {}).get('popular', False)

        # Decide whether to provide pricing and/or storage for this specific plan
        # This occurs if pricing/storage was explicitly requested, OR if no specific info type was requested (general plan inquiry)
        should_detail_pricing_storage = intents['request_pricing'] or intents['request_storage'] or \
                                       not any(intents[k] for k in ['request_pricing', 'request_storage', 
                                                                   'request_platforms', 'request_features', 'request_popular_plan'])
        
        if should_detail_pricing_storage:
            price_info = parsed_kb['pricing'].get(plan)
            storage_info = parsed_kb['storage_limits'].get(plan)

            if price_info:
                price_text = price_info['details'].strip()
                # Remove '(most popular)' tag if it was already handled or not specifically requested
                if is_popular_plan and (intents['request_popular_plan'] or "most popular" in question_lower):
                     price_text = price_text.replace('(most popular)', '').strip()
                plan_description_parts.append(f"costs {price_text}")
            
            if storage_info:
                plan_description_parts.append(f"includes {storage_info} of storage")
            
            if plan_description_parts:
                combined_description = " and ".join(plan_description_parts)
                response_parts.append(f"The {plan.capitalize()} plan {combined_description}.")
            elif intents['request_pricing'] or intents['request_storage']: # If specifically asked but no data
                 response_parts.append(f"I found the {plan.capitalize()} plan, but cannot provide specific pricing or storage details for it.")

    # 4. Handle general pricing query (if not already handled by specific plans)
    if intents['general_pricing_query'] and not plans_to_detail: # Only if general pricing was asked AND no specific plans were detailed
        if parsed_kb['pricing']:
            pricing_statements = []
            for plan, details in parsed_kb['pricing'].items():
                price_info = details['details'].replace('(most popular)', '').strip() # Remove popular tag for general list
                pricing_statements.append(f"{plan.capitalize()}: {price_info}")
            response_parts.append(f"{product_name} offers the following plans: {'; '.join(pricing_statements)}.")
        else:
            response_parts.append(f"I don't have detailed pricing information for {product_name}.")

    # 5. Handle general storage query (if not already handled by specific plans)
    if intents['general_storage_query'] and not plans_to_detail: # Only if general storage was asked AND no specific plans were detailed
        if parsed_kb['storage_limits']:
            storage_statements = []
            for plan, details in parsed_kb['storage_limits'].items():
                storage_statements.append(f"{plan.capitalize()}: {details}")
            response_parts.append(f"{product_name} offers the following storage limits: {'; '.join(storage_statements)}.")
        else:
            response_parts.append(f"I don't have detailed storage limit information for {product_name}.")

    # 6. Handle Supported Platforms
    if intents['request_platforms']:
        if parsed_kb['supported_platforms']:
            response_parts.append(f"{product_name} supports the following platforms: {', '.join(parsed_kb['supported_platforms'])}.")
        else:
            response_parts.append(f"I don't have information about supported platforms for {product_name}.")

    # 7. Handle Key Features
    if intents['request_features']:
        if parsed_kb['key_features']:
            response_parts.append(f"Key features of {product_name} include: {'; '.join(parsed_kb['key_features'])}.")
        else:
            response_parts.append(f"I don't have specific information about the key features of {product_name}.")

    # 8. Product Description (as a last resort if nothing else was added and it was intended)
    if intents['request_product_description'] and not response_parts:
        if parsed_kb['product_description']:
            response_parts.append(f"{parsed_kb['product_name']} is a {parsed_kb['product_description']}.")
        else:
            response_parts.append(f"I can tell you that {parsed_kb['product_name']} is a cloud file synchronization service. How can I help you further?")

    # --- Final Result Aggregation ---
    if response_parts:
        final_answer = " ".join(response_parts)
        # Ensure the final answer ends with appropriate punctuation
        if not final_answer.strip().endswith(('.', '?', '!')):
            final_answer += "."
        return final_answer.strip()
    
    # Default fallback if no relevant information is found or specific intent handled
    return "Thank you for contacting us. I can provide information about pricing, storage, free trials, supported platforms, and key features of CloudSync Pro. Please rephrase your question to be more specific."