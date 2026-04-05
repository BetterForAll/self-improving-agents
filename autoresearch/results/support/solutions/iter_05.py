import re

def answer_question(question, knowledge_base):
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

    # Pricing (stores structured details for easier retrieval)
    pricing_match = re.search(r"Pricing:\n((?:  - .+\n)+)", knowledge_base)
    if pricing_match:
        pricing_data = {}
        for line in pricing_match.group(1).strip().split('\n'):
            plan_match = re.match(r"  - (\w+): (.+)", line)
            if plan_match:
                plan_name = plan_match.group(1).lower()
                details_str = plan_match.group(2).strip()
                pricing_info = {'raw_details': details_str}

                # Extract specific pricing components
                monthly_price_match = re.search(r"\$(\d+)/month", details_str)
                yearly_price_match = re.search(r"\$(\d+)/year", details_str)
                
                if monthly_price_match:
                    pricing_info['monthly_price_value'] = int(monthly_price_match.group(1))
                    pricing_info['monthly_display'] = f"${monthly_price_match.group(1)}/month"
                if yearly_price_match:
                    pricing_info['yearly_price_value'] = int(yearly_price_match.group(1))
                    pricing_info['yearly_display'] = f"${yearly_price_match.group(1)}/year"
                
                if 'per seat' in details_str.lower():
                    pricing_info['per_seat'] = True
                if 'annual billing only' in details_str.lower():
                    pricing_info['annual_billing_only'] = True
                if '(most popular)' in details_str.lower():
                    pricing_info['popular'] = True
                
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
    
    intents = {
        'free_trial': False,
        'popular_plan_query': False, 
        'pricing_for_plans': set(), # Stores specific plans or 'all'
        'storage_for_plans': set(), # Stores specific plans or 'all'
        'platforms': False,
        'features': False,
        'general_plan_inquiry': set(), # Plans mentioned without specific pricing/storage keywords
        'product_description': False
    }

    # Helper to find plan names with word boundaries for accuracy
    def get_plans_from_question_with_boundaries(q_lower, kb_plans):
        found_plans = set()
        for plan_key in kb_plans:
            if re.search(r"\b" + re.escape(plan_key) + r"\b", q_lower):
                found_plans.add(plan_key)
        return sorted(list(found_plans))
    
    all_kb_plans = set(parsed_kb.get('pricing', {}).keys()).union(parsed_kb.get('storage_limits', {}).keys())
    plans_in_q = get_plans_from_question_with_boundaries(question_lower, all_kb_plans)

    # Detect intents
    if any(keyword in question_lower for keyword in ["trial", "free", "demo", "test", "try"]):
        intents['free_trial'] = True

    if "most popular" in question_lower:
        intents['popular_plan_query'] = True
    
    pricing_keywords = ["price", "cost", "how much", "monthly", "annual", "subscription", "pricing"]
    if any(keyword in question_lower for keyword in pricing_keywords):
        if plans_in_q:
            intents['pricing_for_plans'].update(plans_in_q)
        else:
            intents['pricing_for_plans'].add('all')

    storage_keywords = ["storage", "gb", "tb", "space", "limit", "capacity", "how much data"]
    if any(keyword in question_lower for keyword in storage_keywords):
        if plans_in_q:
            intents['storage_for_plans'].update(plans_in_q)
        else:
            intents['storage_for_plans'].add('all')

    if any(keyword in question_lower for keyword in ["platform", "device", "os", "compatible", "support", "work on", "run on", "app"]):
        intents['platforms'] = True

    feature_keywords = ["feature", "what does it do", "can it", "encryption", "sync", "capabilities", "real-time", "end-to-end", "functionality"]
    if any(keyword in question_lower for keyword in feature_keywords):
        intents['features'] = True

    # General Plan Info: If plans are mentioned but no specific pricing/storage intent for them
    for plan in plans_in_q:
        if plan not in intents['pricing_for_plans'] and plan not in intents['storage_for_plans']:
            intents['general_plan_inquiry'].add(plan)
    
    # Product Description: Low priority, only if no other specific intents are detected.
    specific_intents_triggered = any(
        (isinstance(v, bool) and v and k not in ['product_description']) or 
        (isinstance(v, set) and len(v) > 0)
        for k, v in intents.items()
    )
    
    if not specific_intents_triggered and \
       any(kw in question_lower for kw in [product_name.lower(), "what is it", "tell me about", "describe", "info on"]):
        intents['product_description'] = True

    # --- Constructing the Answer based on Detected Intents ---
    response_parts = []
    
    # 1. Product Description (Highest priority if it's the *only* significant intent)
    if intents['product_description'] and not specific_intents_triggered:
        if product_description:
            response_parts.append(f"{product_name} is a {product_description}.")
        else:
            response_parts.append(f"{product_name} is a cloud file synchronization service.")

    # 2. Free Trial
    if intents['free_trial']:
        if 'free_trial' in parsed_kb:
            response_parts.append(f"Yes, {product_name} offers a {parsed_kb['free_trial']}.")
        else:
            response_parts.append(f"I don't have information about a free trial for {product_name}.")

    # 3. Most Popular Plan query
    if intents['popular_plan_query'] and 'pricing' in parsed_kb:
        popular_plan_name = None
        for plan_name, plan_info in parsed_kb['pricing'].items():
            if plan_info.get('popular'):
                popular_plan_name = plan_name
                
                popular_plan_pricing = parsed_kb['pricing'].get(popular_plan_name)
                popular_plan_storage = parsed_kb['storage_limits'].get(popular_plan_name)
                
                popular_details_str_parts = []
                if popular_plan_pricing:
                    pricing_parts = []
                    if popular_plan_pricing.get('monthly_display'):
                        pricing_parts.append(popular_plan_pricing['monthly_display'])
                    if popular_plan_pricing.get('yearly_display'):
                        pricing_parts.append(popular_plan_pricing['yearly_display'])
                    
                    price_str = " or ".join(pricing_parts)
                    if popular_plan_pricing.get('per_seat'):
                        price_str += " per seat"
                    if popular_plan_pricing.get('annual_billing_only'):
                        price_str += " (annual billing only)"
                    
                    if price_str:
                        popular_details_str_parts.append(f"costs {price_str}")
                
                if popular_plan_storage:
                    popular_details_str_parts.append(f"provides {popular_plan_storage} storage")
                
                if popular_details_str_parts:
                    response_parts.append(f"The {popular_plan_name.capitalize()} plan is the most popular, and {', and '.join(popular_details_str_parts)}.")
                else:
                     response_parts.append(f"The {popular_plan_name.capitalize()} plan is the most popular, costing {plan_info['raw_details'].replace('(most popular)', '').strip()}.")
                break
        if not popular_plan_name:
             response_parts.append(f"I don't have information on which plan is most popular for {product_name}.")

    # 4. Specific Plan Inquiries (Pricing, Storage, or General Plan Info)
    # Collect all unique plans that need detailing, excluding 'all' for specific plan logic
    plans_to_detail = sorted(list(intents['pricing_for_plans'].union(intents['storage_for_plans']).union(intents['general_plan_inquiry'])))
    if 'all' in plans_to_detail:
        plans_to_detail.remove('all')

    for plan in plans_to_detail:
        plan_details_list = []
        
        explicitly_pricing = plan in intents['pricing_for_plans']
        explicitly_storage = plan in intents['storage_for_plans']
        general_inquiry = plan in intents['general_plan_inquiry']

        plan_pricing_info = parsed_kb['pricing'].get(plan)
        plan_storage_info = parsed_kb['storage_limits'].get(plan)

        # Pricing details for this plan
        if plan_pricing_info and (explicitly_pricing or general_inquiry):
            pricing_parts = []
            if plan_pricing_info.get('monthly_display'):
                pricing_parts.append(plan_pricing_info['monthly_display'])
            if plan_pricing_info.get('yearly_display'):
                pricing_parts.append(plan_pricing_info['yearly_display'])
            
            price_str = " or ".join(pricing_parts) if pricing_parts else plan_pricing_info.get('raw_details', 'price not specified')

            if plan_pricing_info.get('per_seat'):
                price_str += " per seat"
            if plan_pricing_info.get('annual_billing_only'):
                price_str += " (annual billing only)"
            
            # Remove '(most popular)' tag if it's not the primary intent for popular plan
            if plan_pricing_info.get('popular') and not intents['popular_plan_query']:
                price_str = price_str.replace('(most popular)', '').strip()
            
            plan_details_list.append(f"costs {price_str}")
        elif explicitly_pricing:
            plan_details_list.append(f"pricing details are not available for the {plan.capitalize()} plan")

        # Storage details for this plan
        if plan_storage_info and (explicitly_storage or general_inquiry):
            plan_details_list.append(f"offers {plan_storage_info} storage")
        elif explicitly_storage:
            plan_details_list.append(f"storage limits are not available for the {plan.capitalize()} plan")

        if plan_details_list:
            response_parts.append(f"The {plan.capitalize()} plan {', and '.join(plan_details_list)}.")
        elif general_inquiry: 
            response_parts.append(f"I found the {plan.capitalize()} plan, but cannot provide specific details for your question.")


    # 5. General Pricing (if 'all' was in pricing intent and no specific plans covered above for pricing)
    # Only if 'all' is explicitly requested AND no specific plans' pricing were already included in the response for a pricing query.
    if 'all' in intents['pricing_for_plans'] and not any(p in intents['pricing_for_plans'] for p in plans_to_detail):
        if 'pricing' in parsed_kb:
            pricing_statements = []
            for plan, details in parsed_kb['pricing'].items():
                price_info_str_parts = []
                if details.get('monthly_display'):
                    price_info_str_parts.append(details['monthly_display'])
                if details.get('yearly_display'):
                    price_info_str_parts.append(details['yearly_display'])
                
                price_display = " or ".join(price_info_str_parts) if price_info_str_parts else details.get('raw_details', 'price not specified')

                if details.get('per_seat'):
                    price_display += " per seat"
                if details.get('annual_billing_only'):
                    price_display += " (annual billing only)"
                
                pricing_statements.append(f"{plan.capitalize()}: {price_display.replace('(most popular)', '').strip()}")
            response_parts.append(f"{product_name} offers the following plans: {'; '.join(pricing_statements)}.")
        else:
            response_parts.append(f"I don't have detailed pricing information for {product_name}.")

    # 6. General Storage (if 'all' was in storage intent and no specific plans covered above for storage)
    # Only if 'all' is explicitly requested AND no specific plans' storage were already included in the response for a storage query.
    if 'all' in intents['storage_for_plans'] and not any(p in intents['storage_for_plans'] for p in plans_to_detail):
        if 'storage_limits' in parsed_kb:
            storage_statements = []
            for plan, details in parsed_kb['storage_limits'].items():
                storage_statements.append(f"{plan.capitalize()}: {details}")
            response_parts.append(f"{product_name} offers the following storage limits: {'; '.join(storage_statements)}.")
        else:
            response_parts.append(f"I don't have detailed storage limit information for {product_name}.")

    # 7. Supported Platforms
    if intents['platforms']:
        if 'supported_platforms' in parsed_kb:
            response_parts.append(f"{product_name} supports the following platforms: {', '.join(parsed_kb['supported_platforms'])}.")
        else:
            response_parts.append(f"I don't have information about supported platforms for {product_name}.")

    # 8. Key Features
    if intents['features']:
        if 'key_features' in parsed_kb:
            response_parts.append(f"Key features of {product_name} include: {'; '.join(parsed_kb['key_features'])}.")
        else:
            response_parts.append(f"I don't have specific information about the key features of {product_name}.")
            
    # --- Final Result Aggregation ---
    if response_parts:
        final_answer = " ".join(response_parts)
        
        # Ensure proper punctuation at the end, and no double punctuation
        final_answer = final_answer.strip()
        if not final_answer.endswith(('.', '?', '!')):
            final_answer += "."
        
        # Capitalize first letter of the overall response for consistency
        if final_answer:
            final_answer = final_answer[0].upper() + final_answer[1:]

        return final_answer
    
    # Default fallback if no relevant information is found
    return "Thank you for contacting us. I can provide information about pricing, storage, free trials, supported platforms, and key features of CloudSync Pro. Please rephrase your question to be more specific."