def answer_question(question, knowledge_base):
    import re

    # --- Helper for list formatting ---
    def format_list_with_and(items):
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        return f"{', '.join(items[:-1])} and {items[-1]}"

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

    # Pricing (stores structured details)
    pricing_data = {}
    pricing_match = re.search(r"Pricing:\n((?:  - .+\n)+)", knowledge_base)
    if pricing_match:
        for line in pricing_match.group(1).strip().split('\n'):
            plan_match = re.match(r"  - (\w+): (.+)", line)
            if plan_match:
                plan_name = plan_match.group(1).lower()
                details_str = plan_match.group(2).strip()
                pricing_info = {
                    'raw_details': details_str, # Keep original string for fallback
                    'monthly_price_text': None,
                    'yearly_price_text': None,
                    'per_seat': False,
                    'annual_billing_only': False,
                    'popular': False
                }

                # Extract specific price components
                monthly_match = re.search(r"(\$\d+)/month", details_str) # e.g., $9/month, $79/month
                if monthly_match:
                    pricing_info['monthly_price_text'] = monthly_match.group(1)

                yearly_match = re.search(r"(\$\d+)/year", details_str)
                if yearly_match:
                    pricing_info['yearly_price_text'] = yearly_match.group(1)

                if 'per seat' in details_str.lower():
                    pricing_info['per_seat'] = True
                if 'annual billing only' in details_str.lower():
                    pricing_info['annual_billing_only'] = True
                if '(most popular)' in details_str.lower():
                    pricing_info['popular'] = True
                
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
        'plans_mentioned': set(),
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
    
    pricing_keywords = ["price", "cost", "how much", "monthly", "annual", "subscription", "pricing", "plans"]
    if any(keyword in question_lower for keyword in pricing_keywords):
        intents['request_pricing'] = True
        if not intents['plans_mentioned']:
            intents['general_pricing_query'] = True

    storage_keywords = ["storage", "gb", "tb", "space", "limit", "capacity", "how much data"]
    if any(keyword in question_lower for keyword in storage_keywords):
        intents['request_storage'] = True
        if not intents['plans_mentioned']:
            intents['general_storage_query'] = True

    if any(keyword in question_lower for keyword in ["platform", "device", "os", "compatible", "support", "work on", "run on", "app"]):
        intents['request_platforms'] = True

    if any(keyword in question_lower for keyword in ["feature", "what does it do", "can it", "encryption", "sync", "capabilities", "real-time", "end-to-end"]):
        intents['request_features'] = True

    # Product Description: As a fallback if no other strong specific intent is detected
    # Also trigger if explicit "what is CloudSync Pro" type question.
    if not any(intents[key] for key in ['request_free_trial', 'request_popular_plan', 'request_pricing', 
                                        'request_storage', 'request_platforms', 'request_features', 'plans_mentioned']):
        if product_name.lower() in question_lower or "what is" in question_lower or "tell me about" in question_lower or "about" in question_lower:
             intents['request_product_description'] = True

    # --- Constructing the Answer based on Detected Intents ---
    response_parts = []
    # Keep track of what information has been explicitly addressed to avoid redundancy
    addressed_intents_flags = set() 
    addressed_plans = set()

    # 1. Handle specific plans mentioned in the question (combine pricing & storage for them)
    if intents['plans_mentioned']:
        for plan_name in sorted(list(intents['plans_mentioned'])): # Sort for consistent output
            if plan_name not in addressed_plans:
                plan_description_segments = []
                
                price_info = parsed_kb['pricing'].get(plan_name)
                storage_limit = parsed_kb['storage_limits'].get(plan_name)

                # Decide if pricing/storage should be detailed for this specific plan.
                # Detail if explicitly requested, or if it's a general inquiry about the plan.
                should_detail_pricing = intents['request_pricing'] or \
                                        (not any(intents[k] for k in ['request_pricing', 'request_storage', 'request_platforms', 'request_features', 'request_free_trial']))
                should_detail_storage = intents['request_storage'] or \
                                        (not any(intents[k] for k in ['request_pricing', 'request_storage', 'request_platforms', 'request_features', 'request_free_trial']))

                if price_info and should_detail_pricing:
                    price_statement_parts = []
                    if price_info['monthly_price_text']:
                        price_statement_parts.append(f"{price_info['monthly_price_text']}/month")
                    if price_info['yearly_price_text']:
                        price_statement_parts.append(f"{price_info['yearly_price_text']}/year")
                    
                    price_text = ""
                    if price_statement_parts:
                        price_text = " or ".join(price_statement_parts)
                    else: # Fallback to raw if structured extraction failed
                         price_text = price_info['raw_details'].replace('(most popular)', '').strip()

                    if price_text:
                        plan_price_segment = f"costs {price_text}"
                        if price_info['per_seat']:
                            plan_price_segment += " per seat"
                        if price_info['annual_billing_only']:
                            plan_price_segment += ", annual billing only"

                        # Add "most popular" tag only if explicitly asked or it's the Pro plan (which is popular) and a general plan query
                        if price_info['popular'] and (intents['request_popular_plan'] or "most popular" in question_lower or (plan_name == 'pro' and should_detail_pricing)):
                            # If it's already "most popular" and we are detailing it, integrate into the sentence
                            if not plan_price_segment.startswith("is the most popular plan"): # Avoid double mentioning
                                plan_price_segment = f"is the most popular plan, and it {plan_price_segment}"
                        
                        plan_description_segments.append(plan_price_segment)
                        addressed_intents_flags.add('request_pricing')
                        if price_info['popular']:
                             addressed_intents_flags.add('request_popular_plan') # Consider popular plan addressed if mentioned here

                if storage_limit and should_detail_storage:
                    plan_description_segments.append(f"includes {storage_limit} of storage")
                    addressed_intents_flags.add('request_storage')

                if plan_description_segments:
                    combined_description = " and ".join(plan_description_segments)
                    response_parts.append(f"The {plan_name.capitalize()} plan {combined_description}.")
                elif (should_detail_pricing or should_detail_storage): # If specifically asked but no data
                     response_parts.append(f"I found the {plan_name.capitalize()} plan, but cannot provide specific pricing or storage details for it.")
                
                addressed_plans.add(plan_name) # Mark plan as addressed for details

    # 2. Handle Most Popular Plan (if explicitly asked and not yet covered by a specific plan detail)
    if intents['request_popular_plan'] and 'request_popular_plan' not in addressed_intents_flags:
        popular_plan_name = None
        for plan, info in parsed_kb['pricing'].items():
            if info.get('popular'):
                popular_plan_name = plan
                price_statement_parts = []
                if info['monthly_price_text']:
                    price_statement_parts.append(f"{info['monthly_price_text']}/month")
                if info['yearly_price_text']:
                    price_statement_parts.append(f"{info['yearly_price_text']}/year")
                
                price_text = " or ".join(price_statement_parts) if price_statement_parts else info['raw_details'].replace('(most popular)', '').strip()

                popular_response = f"The {plan.capitalize()} plan is the most popular, costing {price_text}"
                if info['per_seat']:
                    popular_response += " per seat"
                if info['annual_billing_only']:
                     popular_response += ", with annual billing only"
                popular_response += "."
                response_parts.append(popular_response)
                addressed_intents_flags.add('request_popular_plan')
                if 'request_pricing' not in addressed_intents_flags:
                    addressed_intents_flags.add('request_pricing') # Also imply pricing addressed
                break
        if not popular_plan_name:
             response_parts.append(f"I don't have information on which plan is most popular for {product_name}.")

    # 3. Handle General Pricing Query (if requested and not covered by specific plans)
    if intents['general_pricing_query'] and 'request_pricing' not in addressed_intents_flags:
        if parsed_kb['pricing']:
            pricing_statements = []
            for plan, details in parsed_kb['pricing'].items():
                price_statement_parts = []
                if details['monthly_price_text']:
                    price_statement_parts.append(f"{details['monthly_price_text']}/month")
                if details['yearly_price_text']:
                    price_statement_parts.append(f"{details['yearly_price_text']}/year")
                
                price_text = " or ".join(price_statement_parts) if price_statement_parts else details['raw_details'].replace('(most popular)', '').strip()

                plan_pricing_summary = f"{plan.capitalize()}: {price_text}"
                if details['per_seat']:
                    plan_pricing_summary += " per seat"
                if details['annual_billing_only']:
                    plan_pricing_summary += ", annual billing only"
                if details['popular'] and 'request_popular_plan' not in addressed_intents_flags: # Only add '(most popular)' if general pricing asked and not already handled
                    plan_pricing_summary += " (most popular)"
                pricing_statements.append(plan_pricing_summary)
            response_parts.append(f"{product_name} offers the following plans: {'; '.join(pricing_statements)}.")
            addressed_intents_flags.add('request_pricing')
        else:
            response_parts.append(f"I don't have detailed pricing information for {product_name}.")

    # 4. Handle General Storage Query (if requested and not covered by specific plans)
    if intents['general_storage_query'] and 'request_storage' not in addressed_intents_flags:
        if parsed_kb['storage_limits']:
            storage_statements = []
            for plan, details in parsed_kb['storage_limits'].items():
                storage_statements.append(f"{plan.capitalize()}: {details}")
            response_parts.append(f"{product_name} offers the following storage limits: {'; '.join(storage_statements)}.")
            addressed_intents_flags.add('request_storage')
        else:
            response_parts.append(f"I don't have detailed storage limit information for {product_name}.")

    # 5. Handle Free Trial
    if intents['request_free_trial'] and 'request_free_trial' not in addressed_intents_flags:
        if parsed_kb['free_trial']:
            response_parts.append(f"Yes, {product_name} offers a 14-day free trial on any plan, with no credit card required.")
        else:
            response_parts.append(f"I don't have information about a free trial for {product_name}.")
        addressed_intents_flags.add('request_free_trial')

    # 6. Handle Supported Platforms
    if intents['request_platforms'] and 'request_platforms' not in addressed_intents_flags:
        if parsed_kb['supported_platforms']:
            formatted_platforms = format_list_with_and(parsed_kb['supported_platforms'])
            response_parts.append(f"{product_name} is supported on {formatted_platforms}.")
        else:
            response_parts.append(f"I don't have information about supported platforms for {product_name}.")
        addressed_intents_flags.add('request_platforms')

    # 7. Handle Key Features
    if intents['request_features'] and 'request_features' not in addressed_intents_flags:
        if parsed_kb['key_features']:
            response_parts.append(f"Key features of {product_name} include: {'; '.join(parsed_kb['key_features'])}.")
        else:
            response_parts.append(f"I don't have specific information about the key features of {product_name}.")
        addressed_intents_flags.add('request_features')

    # 8. Product Description (as a last resort if nothing else was added and it was intended)
    if intents['request_product_description'] and not response_parts: # Only if nothing else was more specific
        if parsed_kb['product_description']:
            response_parts.append(f"{parsed_kb['product_name']} is a {parsed_kb['product_description']}.")
        else:
            response_parts.append(f"I can tell you that {parsed_kb['product_name']} is a cloud file synchronization service. How can I help you further?")

    # --- Final Result Aggregation ---
    if response_parts:
        final_answer = " ".join(response_parts).strip()
        # Ensure the final answer ends with appropriate punctuation
        if not final_answer.endswith(('.', '?', '!')):
            final_answer += "."
        return final_answer
    
    # Default fallback if no relevant information is found or specific intent handled
    return "Thank you for contacting us. I can provide information about pricing, storage, free trials, supported platforms, and key features of CloudSync Pro. Please rephrase your question to be more specific."