def answer_question(question, knowledge_base):
    import re

    # --- Knowledge Base Parsing ---
    parsed_kb = {}

    # Default product name and description (will be updated if found in KB)
    product_name = "CloudSync Pro"
    product_description = "Cloud File Synchronization Service"

    product_match = re.search(r"Product: (.+?) -- (.+)", knowledge_base)
    if product_match:
        product_name = product_match.group(1).strip()
        product_description = product_match.group(2).strip()
    parsed_kb['product_name'] = product_name
    parsed_kb['product_description'] = product_description

    # Pricing (stores details and flags like 'popular', 'annual_billing_only')
    pricing_match = re.search(r"Pricing:\n((?:  - .+\n)+)", knowledge_base)
    if pricing_match:
        pricing_data = {}
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
        parsed_kb['pricing'] = pricing_data

    # Storage Limits
    storage_match = re.search(r"Storage Limits:\n((?:  - .+\n)+)", knowledge_base)
    if storage_match:
        storage_data = {}
        for line in storage_match.group(1).strip().split('\n'):
            plan_match = re.match(r"  - (\w+): (.+)", line)
            if plan_match:
                storage_data[plan_match.group(1).lower()] = plan_match.group(2).strip()
        parsed_kb['storage_limits'] = storage_data

    # Free Trial
    free_trial_match = re.search(r"Free Trial: (.+)", knowledge_base)
    if free_trial_match:
        parsed_kb['free_trial'] = free_trial_match.group(1).strip()

    # Supported Platforms
    platforms_match = re.search(r"Supported Platforms: (.+)", knowledge_base)
    if platforms_match:
        parsed_kb['supported_platforms'] = [p.strip() for p in platforms_match.group(1).split(',')]

    # Key Features
    features_match = re.search(r"Key Features:\n((?:  - .+\n)+)", knowledge_base)
    if features_match:
        features_list = []
        for line in features_match.group(1).strip().split('\n'):
            feature_match = re.match(r"  - (.+)", line)
            if feature_match:
                features_list.append(feature_match.group(1).strip())
        parsed_kb['key_features'] = features_list

    # --- Intent Detection ---
    question_lower = question.lower()
    response_parts = []
    
    # Structure to hold detected intents and associated data (e.g., specific plans)
    intents = {
        'free_trial': False,
        'popular_plan': False,
        'pricing': [],  # List of plans for which pricing is requested, or ['all'] for general pricing
        'storage': [],  # List of plans for which storage is requested, or ['all'] for general storage
        'platforms': False,
        'features': False,
        'general_plan_info': [], # Plans mentioned without specific pricing/storage/feature keywords
        'product_description': False
    }

    def get_plans_from_question(q_lower):
        found_plans = []
        # Prioritize full plan names to avoid partial matches (e.g., 'pro' in 'promote')
        for plan_key in ["enterprise", "personal", "pro"]: # Longer names first
            if plan_key in q_lower:
                found_plans.append(plan_key)
        # Use a set to avoid duplicates if multiple keywords match for the same plan
        return sorted(list(set(found_plans)))
    
    plans_in_q = get_plans_from_question(question_lower)

    # Detect all possible intents
    if any(keyword in question_lower for keyword in ["trial", "free", "demo", "test", "try"]):
        intents['free_trial'] = True

    if "most popular" in question_lower:
        intents['popular_plan'] = True
    
    if any(keyword in question_lower for keyword in ["price", "cost", "how much", "monthly", "annual", "subscription", "pricing"]):
        intents['pricing'] = plans_in_q if plans_in_q else ['all']

    if any(keyword in question_lower for keyword in ["storage", "gb", "tb", "space", "limit", "capacity"]):
        intents['storage'] = plans_in_q if plans_in_q else ['all']

    if any(keyword in question_lower for keyword in ["platform", "device", "os", "compatible", "support", "work on", "run on", "app"]):
        intents['platforms'] = True

    if any(keyword in question_lower for keyword in ["feature", "what does it do", "can it", "encryption", "sync", "capabilities", "real-time", "end-to-end"]):
        intents['features'] = True

    # General Plan Info: If plans are mentioned but no specific intent (pricing/storage/features) for them
    # Note: Check against the plans_in_q, not current intents['pricing']/storage'] as those might be ['all']
    # which doesn't mean a specific plan was requested.
    plans_with_specific_intent = set(intents['pricing']).union(set(intents['storage']))
    for plan in plans_in_q:
        if plan not in plans_with_specific_intent:
            intents['general_plan_info'].append(plan)
    intents['general_plan_info'] = sorted(list(set(intents['general_plan_info']))) # Ensure unique and sorted

    # Product Description: If no other specific intent detected and question mentions product or is general inquiry
    if not any(v for k,v in intents.items() if k not in ['pricing', 'storage', 'general_plan_info']) \
        and not (intents['pricing'] or intents['storage'] or intents['general_plan_info']) \
        and (product_name.lower() in question_lower or "what is it" in question_lower or "tell me about cloudsync pro" in question_lower):
        intents['product_description'] = True

    # --- Constructing the Answer based on Detected Intents ---
    
    # 1. Free Trial
    if intents['free_trial']:
        if 'free_trial' in parsed_kb:
            response_parts.append(f"Yes, {product_name} offers a {parsed_kb['free_trial']}.")
        else:
            response_parts.append(f"I don't have information about a free trial for {product_name}.")

    # 2. Most Popular Plan
    if intents['popular_plan'] and 'pricing' in parsed_kb:
        popular_plan_name = None
        for plan_name, plan_info in parsed_kb['pricing'].items():
            if plan_info.get('popular'):
                popular_plan_name = plan_name
                response_parts.append(f"The {plan_name.capitalize()} plan is the most popular, costing {plan_info['details'].replace('(most popular)', '').strip()}.")
                break
        if not popular_plan_name:
             response_parts.append(f"I don't have information on which plan is most popular for {product_name}.")

    # 3. Plan-specific Pricing/Storage/General Info
    # Combine all plans that need specific detailing
    plans_to_detail = sorted(list(set(intents['pricing'] + intents['storage'] + intents['general_plan_info'])))
    if 'all' in plans_to_detail:
        plans_to_detail.remove('all') # 'all' is handled as a general query later

    for plan in plans_to_detail:
        plan_specific_details = []
        
        is_pricing_requested_for_plan = plan in intents['pricing']
        is_storage_requested_for_plan = plan in intents['storage']
        is_general_info_requested_for_plan = plan in intents['general_plan_info']

        # Pricing
        if plan in parsed_kb['pricing'] and (is_pricing_requested_for_plan or is_general_info_requested_for_plan):
            price_info = parsed_kb['pricing'][plan]
            price_details_str = price_info['details'].strip()
            # If the popular plan was already mentioned specifically (or is currently being addressed by the popular intent), remove its tag
            if intents['popular_plan'] and price_info.get('popular'):
                price_details_str = price_details_str.replace('(most popular)', '').strip()
            
            plan_specific_details.append(f"price: {price_details_str}")
        elif (is_pricing_requested_for_plan or is_general_info_requested_for_plan):
             plan_specific_details.append(f"no specific pricing details available")

        # Storage
        if plan in parsed_kb['storage_limits'] and (is_storage_requested_for_plan or is_general_info_requested_for_plan):
            plan_specific_details.append(f"storage: {parsed_kb['storage_limits'][plan]}")
        elif (is_storage_requested_for_plan or is_general_info_requested_for_plan):
             plan_specific_details.append(f"no specific storage limits available")

        if plan_specific_details:
            if len(plan_specific_details) == 1:
                response_parts.append(f"The {plan.capitalize()} plan for {product_name} offers {plan_specific_details[0]}.")
            elif len(plan_specific_details) > 1:
                response_parts.append(f"The {plan.capitalize()} plan for {product_name} offers {'; '.join(plan_specific_details)}.")
        else:
            # Fallback if a plan was mentioned but no info could be extracted for it based on the parsed KB.
            response_parts.append(f"I found the {plan.capitalize()} plan, but cannot provide specific details for your question.")

    # 4. General Pricing (if 'all' was in pricing intent and no specific plans covered above)
    if 'all' in intents['pricing'] and not plans_to_detail:
        if 'pricing' in parsed_kb:
            pricing_statements = []
            for plan, details in parsed_kb['pricing'].items():
                price_info = details['details'].replace('(most popular)', '').strip() # Remove popular tag for general list
                pricing_statements.append(f"{plan.capitalize()}: {price_info}")
            response_parts.append(f"{product_name} offers the following plans: {'; '.join(pricing_statements)}.")
        else:
            response_parts.append(f"I don't have detailed pricing information for {product_name}.")

    # 5. General Storage (if 'all' was in storage intent and no specific plans covered above)
    if 'all' in intents['storage'] and not plans_to_detail:
        if 'storage_limits' in parsed_kb:
            storage_statements = []
            for plan, details in parsed_kb['storage_limits'].items():
                storage_statements.append(f"{plan.capitalize()}: {details}")
            response_parts.append(f"{product_name} offers the following storage limits: {'; '.join(storage_statements)}.")
        else:
            response_parts.append(f"I don't have detailed storage limit information for {product_name}.")

    # 6. Supported Platforms
    if intents['platforms']:
        if 'supported_platforms' in parsed_kb:
            response_parts.append(f"{product_name} supports the following platforms: {', '.join(parsed_kb['supported_platforms'])}.")
        else:
            response_parts.append(f"I don't have information about supported platforms for {product_name}.")

    # 7. Key Features
    if intents['features']:
        if 'key_features' in parsed_kb:
            response_parts.append(f"Key features of {product_name} include: {'; '.join(parsed_kb['key_features'])}.")
        else:
            response_parts.append(f"I don't have specific information about the key features of {product_name}.")

    # 8. Product Description (as a last resort if nothing else was added)
    if intents['product_description'] and not response_parts:
        if product_description:
            response_parts.append(f"{product_name} is a {product_description}.")
        else:
            response_parts.append(f"{product_name} is a cloud file synchronization service. How can I help you further?")

    # --- Final Result Aggregation ---
    if response_parts:
        final_answer = " ".join(response_parts)
        # Ensure the final answer ends with appropriate punctuation
        if not final_answer.strip().endswith(('.', '?', '!')):
            final_answer += "."
        return final_answer.strip()
    
    # Default fallback if no relevant information is found
    return "Thank you for contacting us. I can provide information about pricing, storage, free trials, supported platforms, and key features of CloudSync Pro. Please rephrase your question to be more specific."