def answer_question(question, knowledge_base):
    import re  # Import re here to ensure it's self-contained within the function definition

    parsed_kb = {}

    # --- Knowledge Base Parsing ---
    # Product Name and Description
    product_match = re.search(r"Product: (.+?) -- (.+)", knowledge_base)
    if product_match:
        parsed_kb['product_name'] = product_match.group(1).strip()
        parsed_kb['product_description'] = product_match.group(2).strip()
    product_name = parsed_kb.get('product_name', 'CloudSync Pro') # Default if not parsed or missing

    # Pricing
    pricing_match = re.search(r"Pricing:\n((?:  - .+\n)+)", knowledge_base)
    if pricing_match:
        pricing_data = {}
        for line in pricing_match.group(1).strip().split('\n'):
            plan_match = re.match(r"  - (\w+): (.+)", line)
            if plan_match:
                pricing_data[plan_match.group(1).lower()] = plan_match.group(2).strip()
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

    # --- Intent Detection and Answering ---
    question_lower = question.lower()

    # Helper to find plan name in the question
    def get_plan_from_question(q_lower):
        for plan_key in ["personal", "pro", "enterprise"]:
            if plan_key in q_lower:
                return plan_key
        return None

    # Free Trial
    if any(keyword in question_lower for keyword in ["trial", "free", "demo", "test", "try"]):
        if 'free_trial' in parsed_kb:
            return f"Yes, {product_name} offers a {parsed_kb['free_trial']}."
        return f"I don't have information about a free trial for {product_name}."

    # Pricing
    if any(keyword in question_lower for keyword in ["price", "cost", "how much", "monthly", "annual", "plan", "subscription", "pricing"]):
        found_plan = get_plan_from_question(question_lower)
        if 'pricing' in parsed_kb:
            if found_plan:
                if found_plan in parsed_kb['pricing']:
                    return f"The {found_plan.capitalize()} plan for {product_name} costs {parsed_kb['pricing'][found_plan]}."
                else:
                    return f"I don't have specific pricing details for the {found_plan.capitalize()} plan for {product_name}."
            else: # General pricing query, list all plans
                pricing_statements = []
                for plan, details in parsed_kb['pricing'].items():
                    pricing_statements.append(f"{plan.capitalize()}: {details}")
                return f"{product_name} offers the following plans: {'; '.join(pricing_statements)}."
        return f"I don't have detailed pricing information for {product_name}."

    # Storage Limits
    if any(keyword in question_lower for keyword in ["storage", "gb", "tb", "space", "limit", "capacity"]):
        found_plan = get_plan_from_question(question_lower)
        if 'storage_limits' in parsed_kb:
            if found_plan:
                if found_plan in parsed_kb['storage_limits']:
                    return f"The {found_plan.capitalize()} plan for {product_name} includes {parsed_kb['storage_limits'][found_plan]} of storage."
                else:
                    return f"I don't have specific storage limits for the {found_plan.capitalize()} plan for {product_name}."
            else: # General storage query, list all limits
                storage_statements = []
                for plan, details in parsed_kb['storage_limits'].items():
                    storage_statements.append(f"{plan.capitalize()}: {details}")
                return f"{product_name} offers the following storage limits: {'; '.join(storage_statements)}."
        return f"I don't have detailed storage limit information for {product_name}."

    # Supported Platforms
    if any(keyword in question_lower for keyword in ["platform", "device", "os", "compatible", "support", "work on", "run on", "app"]):
        if 'supported_platforms' in parsed_kb:
            return f"{product_name} supports the following platforms: {', '.join(parsed_kb['supported_platforms'])}."
        return f"I don't have information about supported platforms for {product_name}."

    # Key Features
    if any(keyword in question_lower for keyword in ["feature", "what does it do", "can it", "encryption", "sync", "capabilities", "real-time", "end-to-end"]):
        if 'key_features' in parsed_kb:
            return f"Key features of {product_name} include: {'; '.join(parsed_kb['key_features'])}."
        return f"I don't have specific information about the key features of {product_name}."
    
    # General Product Info / Plan overview (if a plan is mentioned but no specific intent keyword)
    found_plan = get_plan_from_question(question_lower)
    if found_plan:
        plan_summary_parts = [f"Here's some information about the {found_plan.capitalize()} plan:"]
        if 'pricing' in parsed_kb and found_plan in parsed_kb['pricing']:
            plan_summary_parts.append(f"Price: {parsed_kb['pricing'][found_plan]}.")
        if 'storage_limits' in parsed_kb and found_plan in parsed_kb['storage_limits']:
            plan_summary_parts.append(f"Storage: {parsed_kb['storage_limits'][found_plan]}.")
        
        if len(plan_summary_parts) > 1: # If any specific info was added
            return " ".join(plan_summary_parts)
        return f"I found information about the {found_plan.capitalize()} plan, but cannot provide a detailed summary for your specific question. Please clarify if you're asking about pricing, storage, or features."

    # If no specific intent found, but question mentions the product name or is a general inquiry about it
    if product_name.lower() in question_lower or "what is it" in question_lower or "tell me about cloudsync pro" in question_lower:
        if 'product_description' in parsed_kb:
            return f"{product_name} is a {parsed_kb['product_description']}."
        # Fallback if description isn't parsed
        return f"{product_name} is a cloud file synchronization service. How can I help you further?"

    # Default fallback if no relevant information is found
    return "Thank you for contacting us. I can provide information about pricing, storage, free trials, supported platforms, and key features of CloudSync Pro. Please rephrase your question to be more specific."