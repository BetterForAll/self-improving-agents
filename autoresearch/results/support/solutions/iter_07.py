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
    parsed_kb['pricing'] = pricing_data

    # Storage Limits
    storage_data = {}
    storage_match = re.search(r"Storage Limits:\n((?:  - .+\n)+)", knowledge_base)
    if storage_match:
        for line in storage_match.group(1).strip().split('\n'):
            plan_match = re.match(r"  - (\w+): (.+)", line)
            if plan_match:
                storage_data[plan_match.group(1).lower()] = plan_match.group(2).strip()
    parsed_kb['storage_limits'] = storage_data

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
    parsed_kb['key_features'] = features_list

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
        'general_storage_query': False, # User asked for storage, but not for a specific plan
        'has_specific_plan_price_query': False, # Track if user specifically asked for a plan's price
        'has_specific_plan_storage_query': False # Track if user specifically asked for a plan's storage
    }

    # Helper to find plan names robustly using word boundaries and common variations
    all_plan_names_in_kb = list(parsed_kb['pricing'].keys()) # Get plan names in their original order for consistency
    all_plan_names_for_regex = sorted(all_plan_names_in_kb, key=len, reverse=True) # Sort by length for regex to match longer names first

    if all_plan_names_for_regex:
        # Create patterns for "plan_name" and "plan_name plan"
        plan_name_patterns_raw = [re.escape(p) for p in all_plan_names_for_regex] + \
                                 [re.escape(p) + r'\s*plan' for p in all_plan_names_for_regex]
        plan_name_pattern = r'\b(' + '|'.join(plan_name_patterns_raw) + r')\b'
        found_plans_raw = re.findall(plan_name_pattern, question_lower)
        
        # Normalize found plans (e.g., "personal plan" -> "personal")
        for p_raw in found_plans_raw:
            for plan_key in all_plan_names_in_kb:
                if plan_key in p_raw: # Check if the actual plan key is part of the matched string
                    intents['plans_mentioned'].add(plan_key)
                    break
    
    # Check for specific plan + pricing/storage keywords
    for plan in intents['plans_mentioned']:
        plan_regex_pattern = r'\b' + re.escape(plan) + r'(?:\s*plan)?\b' # Matches "plan" or "plan plan"
        
        pricing_keywords_regex = r'(?:price|cost|how much|monthly|annual|subscription|pricing)'
        if re.search(f"{plan_regex_pattern}.*?{pricing_keywords_regex}", question_lower) or \
           re.search(f"{pricing_keywords_regex}.*?{plan_regex_pattern}", question_lower):
            intents['has_specific_plan_price_query'] = True
            intents['request_pricing'] = True # Also set general pricing flag
        
        storage_keywords_regex = r'(?:storage|gb|tb|space|limit|capacity)'
        if re.search(f"{plan_regex_pattern}.*?{storage_keywords_regex}", question_lower) or \
           re.search(f"{storage_keywords_regex}.*?{plan_regex_pattern}", question_lower):
            intents['has_specific_plan_storage_query'] = True
            intents['request_storage'] = True # Also set general storage flag

    # Detect primary intents
    if any(keyword in question_lower for keyword in ["trial", "free", "demo", "test", "try"]):
        intents['request_free_trial'] = True

    if "most popular" in question_lower:
        intents['request_popular_plan'] = True
    
    pricing_keywords = ["price", "cost", "how much", "monthly", "annual", "subscription", "pricing"]
    if any(keyword in question_lower for keyword in pricing_keywords):
        intents['request_pricing'] = True
        if not intents['has_specific_plan_price_query']: # Only set general if no specific plan pricing was found
            intents['general_pricing_query'] = True

    storage_keywords = ["storage", "gb", "tb", "space", "limit", "capacity"]
    if any(keyword in question_lower for keyword in storage_keywords):
        intents['request_storage'] = True
        if not intents['has_specific_plan_storage_query']: # Only set general if no specific plan storage was found
            intents['general_storage_query'] = True

    if any(keyword in question_lower for keyword in ["platform", "device", "os", "compatible", "support", "work on", "run on", "app"]):
        intents['request_platforms'] = True

    if any(keyword in question_lower for keyword in ["feature", "what does it do", "can it", "encryption", "sync", "capabilities", "real-time", "end-to-end"]):
        intents['request_features'] = True

    # Product Description: Explicit intent if no *other specific* intent is strong
    # This intent is typically for broad questions like "What is CloudSync Pro?"
    if any(keyword in question_lower for keyword in ["what is", "tell me about", "describe", product_name.lower()]):
        if not (intents['request_free_trial'] or intents['request_popular_plan'] or intents['request_pricing'] or
                intents['request_storage'] or intents['request_platforms'] or intents['request_features'] or
                intents['plans_mentioned']):
            intents['request_product_description'] = True

    # --- Constructing the Answer based on Detected Intents ---
    response_parts = []
    
    # Track which general queries have been sufficiently answered by specific plan details
    general_pricing_answered = False
    general_storage_answered = False
    popular_plan_handled_directly = False # Flag to prevent redundancy if "most popular" is asked explicitly

    # 1. Handle Free Trial
    if intents['request_free_trial']:
        if parsed_kb['free_trial']:
            response_parts.append(f"Yes, {product_name} offers a {parsed_kb['free_trial']}.")
        else:
            response_parts.append(f"I don't have information about a free trial for {product_name}.")

    # 2. Handle Most Popular Plan (if explicitly requested)
    popular_plan_name = None
    popular_plan_info = None
    for plan_name, plan_info in parsed_kb['pricing'].items():
        if plan_info.get('popular'):
            popular_plan_name = plan_name
            popular_plan_info = plan_info
            break

    if intents['request_popular_plan'] and popular_plan_name:
        price_text = popular_plan_info['details'].replace('(most popular)', '').strip()
        response_parts.append(f"The {popular_plan_name.capitalize()} plan is the most popular, costing {price_text}.")
        intents['plans_mentioned'].add(popular_plan_name) # Ensure it gets processed for full details if needed
        popular_plan_handled_directly = True # Mark as handled to avoid re-stating "most popular" later

    # 3. Handle specific plans (combine pricing, storage, or general info about each mentioned plan)
    # Sort plans alphabetically for consistent output order
    plans_to_process = sorted(list(intents['plans_mentioned']))

    for plan in plans_to_process:
        # Check if plan exists in KB
        if plan not in parsed_kb['pricing'] and plan not in parsed_kb['storage_limits']:
            response_parts.append(f"I don't have information about a '{plan.capitalize()}' plan.")
            continue
        
        plan_description_parts = []
        is_popular = parsed_kb['pricing'].get(plan, {}).get('popular', False)

        # Special handling if this is the popular plan and it was already handled directly
        if popular_plan_handled_directly and plan == popular_plan_name:
            # If storage was also specifically requested for this popular plan, and wasn't part of the direct popular plan answer
            if intents['has_specific_plan_storage_query'] and parsed_kb['storage_limits'].get(plan):
                storage_info = parsed_kb['storage_limits'][plan]
                response_parts.append(f"For the {plan.capitalize()} plan, it includes {storage_info} of storage.")
                general_storage_answered = True # This plan's storage is covered
            continue # Skip further processing for this plan's pricing/storage to avoid redundancy

        # Decide whether to provide pricing for this specific plan
        should_add_pricing = (intents['has_specific_plan_price_query'] and plan in intents['plans_mentioned']) or \
                             (not intents['request_pricing'] and not intents['request_storage'] and plan in intents['plans_mentioned']) # General query about plan

        if parsed_kb['pricing'].get(plan) and (should_add_pricing or (intents['general_pricing_query'] and not general_pricing_answered)):
            price_info = parsed_kb['pricing'][plan]
            price_text = price_info['details'].strip().replace('(most popular)', '').strip() # Remove popular tag if present

            if is_popular and not intents['request_popular_plan'] and 'most popular' not in question_lower:
                plan_description_parts.append(f"is the most popular plan, costing {price_text}")
            else:
                plan_description_parts.append(f"costs {price_text}")
            
            # If general pricing was requested, mark it as potentially answered if this covers it
            if intents['general_pricing_query'] and len(plans_to_process) == len(parsed_kb['pricing']):
                general_pricing_answered = True

        # Decide whether to provide storage for this specific plan
        should_add_storage = (intents['has_specific_plan_storage_query'] and plan in intents['plans_mentioned']) or \
                             (not intents['request_pricing'] and not intents['request_storage'] and plan in intents['plans_mentioned']) # General query about plan

        if parsed_kb['storage_limits'].get(plan) and (should_add_storage or (intents['general_storage_query'] and not general_storage_answered)):
            storage_info = parsed_kb['storage_limits'][plan]
            plan_description_parts.append(f"includes {storage_info} of storage")
            
            # If general storage was requested, mark it as potentially answered
            if intents['general_storage_query'] and len(plans_to_process) == len(parsed_kb['storage_limits']):
                general_storage_answered = True

        if plan_description_parts:
            combined_description = " and ".join(plan_description_parts)
            response_parts.append(f"The {plan.capitalize()} plan {combined_description}.")
        elif (intents['has_specific_plan_price_query'] or intents['has_specific_plan_storage_query']):
            # If specific price/storage was asked but no data was found for it
            info_missing = []
            if intents['has_specific_plan_price_query'] and not parsed_kb['pricing'].get(plan): info_missing.append("pricing")
            if intents['has_specific_plan_storage_query'] and not parsed_kb['storage_limits'].get(plan): info_missing.append("storage")
            if info_missing:
                response_parts.append(f"I found the {plan.capitalize()} plan, but cannot provide specific {' or '.join(info_missing)} details for it.")

    # 4. Handle general pricing query (if not already handled by specific plans or general_pricing_answered)
    if intents['general_pricing_query'] and not general_pricing_answered:
        if parsed_kb['pricing']:
            pricing_statements = []
            for plan, details in parsed_kb['pricing'].items():
                price_info = details['details'].replace('(most popular)', '').strip()
                pricing_statements.append(f"{plan.capitalize()}: {price_info}")
            response_parts.append(f"{product_name} offers the following plans: {'; '.join(pricing_statements)}.")
        else:
            response_parts.append(f"I don't have detailed pricing information for {product_name}.")

    # 5. Handle general storage query (if not already handled by specific plans or general_storage_answered)
    if intents['general_storage_query'] and not general_storage_answered:
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

    # 8. Product Description (as a fallback if nothing else was added and it was intended)
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