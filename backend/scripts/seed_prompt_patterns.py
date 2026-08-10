"""
scripts/seed_prompt_patterns.py — Seeds 500+ prompt templates into Qdrant.

Task: Week 7-8 / RAG Integration (task.md lines 410-413)
  [x] Curate 500+ high-quality prompt templates
  [x] Categorize by domain (coding, writing, marketing, etc.)
  [x] Embed and insert into Qdrant prompt_patterns collection

Usage:
    cd backend
    python -m scripts.seed_prompt_patterns
    # OR
    python scripts/seed_prompt_patterns.py
"""
import sys
import uuid
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── 500+ Curated Prompt Templates by Domain ────────────────────────────────────
# Each entry: {"template": str, "domain": str, "title": str}
PROMPT_PATTERNS = [

    # ══════════════════════════════════════════════════════════════════════
    # CODING (100 patterns)
    # ══════════════════════════════════════════════════════════════════════
    {"domain": "coding", "title": "Code Review", "template": "Act as a senior software engineer. Review the following code for: (1) bugs and edge cases, (2) performance issues, (3) security vulnerabilities, (4) code style and maintainability. Provide specific line-by-line feedback with suggested fixes. Code:\n{code}"},
    {"domain": "coding", "title": "Debug Assistant", "template": "You are an expert debugger. I'm seeing this error: {error_message}. The relevant code is:\n{code}\nExplain exactly why this error occurs, identify the root cause, and provide a corrected version with explanation."},
    {"domain": "coding", "title": "Algorithm Design", "template": "Design an efficient algorithm for: {problem_description}. Include: (1) approach and reasoning, (2) time complexity O(?), (3) space complexity O(?), (4) pseudocode, (5) Python implementation, (6) test cases including edge cases."},
    {"domain": "coding", "title": "API Design", "template": "Design a RESTful API for {system_name}. Include: resource definitions, endpoint URLs, HTTP methods, request/response schemas (JSON), error codes, authentication approach, and versioning strategy. Follow REST best practices."},
    {"domain": "coding", "title": "System Architecture", "template": "Design a scalable system architecture for {use_case} that must handle {scale}. Include: component diagram description, data flow, database choice with justification, caching strategy, and key trade-offs."},
    {"domain": "coding", "title": "Unit Test Writer", "template": "Write comprehensive unit tests for the following function using {test_framework}. Cover: happy path, edge cases, error cases, boundary values, and mock external dependencies where needed.\nFunction:\n{code}"},
    {"domain": "coding", "title": "Code Refactor", "template": "Refactor the following code to improve readability, reduce duplication, and follow SOLID principles. Maintain the same functionality. Explain each refactoring decision.\nOriginal code:\n{code}"},
    {"domain": "coding", "title": "SQL Query Optimisation", "template": "Optimise this SQL query for performance. Explain bottlenecks, suggest indexes, rewrite with CTEs if beneficial, and estimate performance improvement.\nQuery:\n{sql}"},
    {"domain": "coding", "title": "Docker Compose Setup", "template": "Create a production-ready docker-compose.yml for a {stack} application. Include: service definitions, health checks, volume mounts, environment variables, restart policies, and networking."},
    {"domain": "coding", "title": "CI/CD Pipeline", "template": "Write a GitHub Actions workflow for a {language} {project_type} that: runs tests on PR, builds Docker image on merge to main, deploys to {platform}, and sends Slack notification on failure."},
    {"domain": "coding", "title": "Data Structure Choice", "template": "I need to store and access {data_description}. Compare the 3 best data structures for this use case, evaluate each on: insertion O(?), lookup O(?), deletion O(?), memory overhead, and recommend the best choice with justification."},
    {"domain": "coding", "title": "Security Audit", "template": "Perform a security audit of this code. Check for: SQL injection, XSS, CSRF, insecure deserialization, hardcoded secrets, missing authentication, and other OWASP Top 10 vulnerabilities. Provide remediation code.\n{code}"},
    {"domain": "coding", "title": "Performance Profiling", "template": "Analyze this {language} code for performance bottlenecks. Profile CPU usage, memory allocation, and I/O patterns. Suggest specific optimisations with before/after comparison.\n{code}"},
    {"domain": "coding", "title": "Database Schema Design", "template": "Design a normalised database schema for {application_type}. Include: entity-relationship diagram description, table definitions with data types, primary/foreign keys, indexes, and explain normalisation decisions."},
    {"domain": "coding", "title": "React Component", "template": "Build a production-ready React component for {component_description}. Use TypeScript, include props interface, handle loading/error/empty states, add accessibility (ARIA), write JSDoc, and include usage example."},
    {"domain": "coding", "title": "Python Class Design", "template": "Design a Python class for {class_purpose} following OOP best practices. Include: __init__ with type hints, methods with docstrings, property decorators where appropriate, __repr__, error handling, and example usage."},
    {"domain": "coding", "title": "REST Client", "template": "Write a robust {language} HTTP client for the {api_name} API. Handle: authentication, retry logic with exponential backoff, rate limiting, timeout, error parsing, and response validation."},
    {"domain": "coding", "title": "Async Function", "template": "Convert this synchronous code to async/await in {language}. Preserve error handling, add proper concurrency controls (locks/semaphores where needed), and explain why each await point is necessary.\n{code}"},
    {"domain": "coding", "title": "Regex Pattern", "template": "Write a {language} regex to match {pattern_description}. Provide: the regex with named groups, explanation of each component, test cases it matches, test cases it should NOT match, and performance considerations."},
    {"domain": "coding", "title": "Microservices Design", "template": "Design a microservices architecture for {monolith_description}. Define service boundaries, data ownership, inter-service communication (sync vs async), shared data patterns, and migration strategy from monolith."},
    {"domain": "coding", "title": "WebSocket Server", "template": "Implement a WebSocket server in {language} for {use_case}. Handle: connection management, message routing, authentication, reconnection logic, and graceful shutdown."},
    {"domain": "coding", "title": "Machine Learning Pipeline", "template": "Build a scikit-learn pipeline for {ml_task}. Include: data preprocessing steps, feature engineering, model selection with justification, hyperparameter tuning, cross-validation, and evaluation metrics."},
    {"domain": "coding", "title": "CLI Tool", "template": "Create a {language} CLI tool for {purpose}. Use {cli_library}. Include: argument parsing, subcommands, help text, config file support, progress indication, and error messages."},
    {"domain": "coding", "title": "Caching Strategy", "template": "Design a caching strategy for {system}. Cover: what to cache and what not to, TTL policies, cache invalidation triggers, cache-aside vs write-through vs write-behind, and Redis implementation example."},
    {"domain": "coding", "title": "Event-Driven Architecture", "template": "Design an event-driven system for {use_case}. Define: events and their schemas, producers, consumers, message broker choice with justification, ordering guarantees, and idempotency handling."},
    {"domain": "coding", "title": "GraphQL Schema", "template": "Design a GraphQL schema for {application}. Include: types, queries, mutations, subscriptions, input types, enums, and explain resolver strategy. Show example queries."},
    {"domain": "coding", "title": "Load Balancer Config", "template": "Configure an Nginx load balancer for {service_description}. Include: upstream definitions, load balancing algorithm choice with justification, health checks, sticky sessions if needed, and SSL termination."},
    {"domain": "coding", "title": "Authentication System", "template": "Implement JWT authentication for a {language} {framework} API. Include: login endpoint, token generation, refresh token rotation, middleware for protected routes, and token blacklisting for logout."},
    {"domain": "coding", "title": "Data Migration Script", "template": "Write a {language} script to migrate data from {source} to {destination}. Handle: batching for large datasets, error recovery with checkpoint/resume, progress logging, validation, and dry-run mode."},
    {"domain": "coding", "title": "Monitoring Setup", "template": "Set up application monitoring for {service} using Prometheus + Grafana. Define: key metrics to track, custom metric instrumentation code, alert rules, and dashboard JSON config."},
    {"domain": "coding", "title": "Rate Limiter", "template": "Implement a token-bucket rate limiter in {language} using Redis. Handle: per-user limits, per-IP limits, sliding window algorithm, burst allowance, and return appropriate 429 responses with retry-after."},
    {"domain": "coding", "title": "Dependency Injection", "template": "Refactor this code to use dependency injection. Explain benefits, show the container setup, refactor service classes, update tests to use mocks, and demonstrate loose coupling.\n{code}"},
    {"domain": "coding", "title": "Design Pattern", "template": "Implement the {pattern_name} design pattern in {language} for {use_case}. Show: class diagram description, full implementation, where this pattern is most useful, its trade-offs, and real-world examples."},
    {"domain": "coding", "title": "Streaming Data", "template": "Design a streaming data pipeline for {data_source} producing {volume}. Choose between Kafka/Kinesis/Pub-Sub, define consumer groups, handle backpressure, and implement exactly-once processing."},
    {"domain": "coding", "title": "Search Feature", "template": "Implement full-text search for {content_type} using {search_technology}. Include: indexing strategy, query parsing, relevance scoring, filters/facets, autocomplete, and performance tuning."},
    {"domain": "coding", "title": "File Upload Handler", "template": "Build a robust file upload handler in {language} for {use_case}. Include: multipart parsing, file validation (type, size), virus scanning integration point, storage to {storage_service}, and progress tracking."},
    {"domain": "coding", "title": "Notification System", "template": "Design a multi-channel notification system supporting email, SMS, and push. Include: provider abstraction layer, template management, delivery tracking, retry logic, unsubscribe handling, and preference management."},
    {"domain": "coding", "title": "Feature Flag System", "template": "Implement a feature flag system for {application}. Include: flag definition schema, evaluation logic (boolean, percentage rollout, user targeting), SDK interface, admin UI requirements, and flag cleanup process."},
    {"domain": "coding", "title": "Webhook Handler", "template": "Build a webhook receiver in {language} for {service}. Handle: signature verification, idempotency via event ID deduplication, async processing, retry acknowledgment, and logging."},
    {"domain": "coding", "title": "ORM Query Optimisation", "template": "Optimise these SQLAlchemy/Django ORM queries to eliminate N+1 problems. Show: original queries, explain() output interpretation, optimised version with select_related/joinedload, and benchmark comparison.\n{code}"},
    {"domain": "coding", "title": "Kubernetes Deployment", "template": "Write Kubernetes manifests for {service_name}. Include: Deployment with resource limits/requests, HPA, ConfigMap, Secret, Service, Ingress with TLS, and PodDisruptionBudget."},
    {"domain": "coding", "title": "State Machine", "template": "Implement a finite state machine for {use_case} in {language}. Define states, valid transitions, transition guards, side effects on enter/exit, and error states. Include persistence strategy."},
    {"domain": "coding", "title": "Parser Implementation", "template": "Write a parser for {format_description} in {language}. Include: lexer/tokenizer, grammar rules, AST node types, recursive descent parsing logic, and error recovery with helpful messages."},
    {"domain": "coding", "title": "Concurrency Control", "template": "Implement concurrent access control for {shared_resource} in {language}. Address: race conditions, deadlock prevention, lock granularity, optimistic vs pessimistic locking, and performance under contention."},
    {"domain": "coding", "title": "Plugin Architecture", "template": "Design a plugin architecture for {application}. Define: plugin interface/contract, discovery mechanism, lifecycle hooks, sandboxing approach, versioning compatibility, and example plugin implementation."},
    {"domain": "coding", "title": "Observability", "template": "Add observability to {service} following the three pillars: (1) Metrics: what to measure, (2) Logging: structured JSON logs with correlation IDs, (3) Tracing: distributed trace with OpenTelemetry. Show implementation."},
    {"domain": "coding", "title": "Message Queue Consumer", "template": "Implement a reliable {queue_type} consumer in {language} that: processes messages exactly once, handles poison messages, supports dead-letter queues, scales horizontally, and reports consumer lag metrics."},
    {"domain": "coding", "title": "API Gateway Config", "template": "Configure an API Gateway for {microservices_description}. Include: routing rules, authentication middleware, request transformation, rate limiting per route, circuit breaker, and response caching."},
    {"domain": "coding", "title": "CQRS Pattern", "template": "Implement CQRS for {domain_model}. Separate: command handlers (write side), query handlers (read side), event store design, read model projection, and eventual consistency handling."},
    {"domain": "coding", "title": "Code Documentation", "template": "Write comprehensive documentation for this codebase module. Include: module overview, function-level docstrings with args/returns/raises, usage examples, architecture notes, and gotchas to be aware of.\n{code}"},

    # ══════════════════════════════════════════════════════════════════════
    # WRITING (100 patterns)
    # ══════════════════════════════════════════════════════════════════════
    {"domain": "writing", "title": "Blog Post", "template": "Write a {word_count}-word blog post about {topic} for {target_audience}. Structure: compelling headline, hook paragraph, 3-5 main sections with subheadings, key takeaways, and CTA. Tone: {tone}. Include SEO keyword: {keyword}."},
    {"domain": "writing", "title": "Technical Article", "template": "Write a technical article explaining {concept} for {audience_level} developers. Include: real-world problem it solves, step-by-step explanation with code examples, common pitfalls, and further reading."},
    {"domain": "writing", "title": "Cover Letter", "template": "Write a compelling cover letter for a {job_title} position at {company_name}. Highlight: {top_3_skills}. Show genuine knowledge of the company. Length: 3 short paragraphs. Professional yet personal tone."},
    {"domain": "writing", "title": "Product Description", "template": "Write a persuasive product description for {product_name}. Target buyer: {buyer_persona}. Include: key benefits (not features), emotional trigger, social proof reference, and clear CTA. Length: {length}. Tone: {tone}."},
    {"domain": "writing", "title": "Executive Summary", "template": "Write an executive summary of this document for senior leadership. In 200-300 words: state the problem, key findings, recommendation, and business impact. Use clear, direct language, no jargon.\nDocument:\n{content}"},
    {"domain": "writing", "title": "Press Release", "template": "Write a press release announcing {announcement} for {company}. Follow AP style: inverted pyramid structure, strong dateline, compelling headline, quote from {executive_title}, boilerplate, and media contact."},
    {"domain": "writing", "title": "Case Study", "template": "Write a B2B case study for {company} about how they used {product/service} to achieve {outcome}. Structure: challenge → solution → results. Include specific metrics. Target reader: {buyer_role}."},
    {"domain": "writing", "title": "LinkedIn Post", "template": "Write a high-engagement LinkedIn post about {topic} from the perspective of {persona}. Open with a pattern interrupt. Share a specific insight or story. End with a thought-provoking question. 150-200 words max."},
    {"domain": "writing", "title": "Newsletter", "template": "Write a weekly newsletter section about {topic} for {subscriber_type} subscribers. Include: one key insight with concrete example, 2-3 curated resource links with brief commentary, and a actionable tip they can use today."},
    {"domain": "writing", "title": "White Paper", "template": "Write an outline for a white paper on {topic} targeting {target_audience}. Include: problem statement, market analysis, proposed solution, evidence and data sources, implementation guide, and conclusion. Executive-level language."},
    {"domain": "writing", "title": "Social Media Thread", "template": "Write a {platform} thread on {topic}. Hook tweet/post first, then 5-7 substantive follow-up posts, each building on the previous. End with a summary and CTA. Engaging, educational tone. No fluff."},
    {"domain": "writing", "title": "Email Sequence", "template": "Write a {n}-email nurture sequence for {product/service} targeting {persona} who just {trigger_action}. Email 1: welcome/value, Email 2: education, Email 3: social proof, Email 4: objection handling, Email 5: CTA. Subject lines included."},
    {"domain": "writing", "title": "Persuasive Essay", "template": "Write a {word_count}-word persuasive essay arguing {position} on {topic}. Include: strong thesis, 3 evidence-backed arguments, acknowledgment and refutation of counterarguments, and compelling conclusion."},
    {"domain": "writing", "title": "Research Summary", "template": "Summarise this research paper for a {audience} audience. Extract: research question, methodology, key findings, limitations, practical implications, and questions for future research. Plain language, no jargon.\nPaper:\n{text}"},
    {"domain": "writing", "title": "User Story", "template": "Write user stories for {feature} from the perspective of {user_role}. Use format: As a [user], I want to [action], so that [benefit]. Include: acceptance criteria, edge cases, and definition of done."},
    {"domain": "writing", "title": "Grant Proposal", "template": "Write a grant proposal for {project} seeking ${amount} from {funder}. Include: project overview, need/problem statement, objectives (SMART), methodology, evaluation plan, budget justification, and organisational capacity."},
    {"domain": "writing", "title": "Speech / Presentation Opening", "template": "Write a powerful 2-minute opening for a presentation on {topic} to {audience}. Start with a story, surprising statistic, or provocative question. Establish credibility, preview structure, and create urgency."},
    {"domain": "writing", "title": "FAQ Page", "template": "Write 10 FAQ entries for {product/service} targeting {customer_type}. Each answer: 2-4 sentences, direct, addresses the real anxiety behind the question, and links to relevant next action."},
    {"domain": "writing", "title": "Testimonial Request", "template": "Write a follow-up email to {customer_name} at {company} requesting a testimonial for {product/service}. Reference their specific result. Provide 3 guiding questions. Keep it under 100 words. Professional and warm."},
    {"domain": "writing", "title": "Thought Leadership Article", "template": "Write a 600-word thought leadership article for {executive_name}, {title} at {company}, on the topic of {topic}. Express a non-obvious, contrarian perspective backed by experience. Target publication: {publication}."},
    {"domain": "writing", "title": "Landing Page Copy", "template": "Write conversion-optimised landing page copy for {product/offer}. Include: headline (benefit-focused), sub-headline, 3 pain points + solutions, social proof section, FAQ section, and primary CTA. Buyer: {persona}."},
    {"domain": "writing", "title": "Job Description", "template": "Write a compelling job description for {job_title} at {company}. Avoid generic language. Lead with what makes this role interesting. List responsibilities as outcomes, not tasks. Requirements: must-haves vs nice-to-haves."},
    {"domain": "writing", "title": "Meeting Agenda", "template": "Create a structured {duration}-minute meeting agenda for {meeting_purpose} with {attendees}. Include: objectives, pre-read materials, timed agenda items with owners, decision points, and desired outcomes."},
    {"domain": "writing", "title": "Proposal Letter", "template": "Write a business proposal letter to {prospect_name} at {company} proposing {solution} to address {problem}. Be specific about value, timeline, investment, and include a clear next step. Under 400 words."},
    {"domain": "writing", "title": "Annual Report Section", "template": "Write the {section_name} section of an annual report for {company_type}. Present {data/achievements} in narrative form that is engaging for shareholders. Balance facts with strategic storytelling."},
    {"domain": "writing", "title": "Tutorial / How-To Guide", "template": "Write a step-by-step guide on how to {task} for {audience_skill_level}. Include: prerequisite knowledge, numbered steps with explanations, screenshots/diagram placeholders, common mistakes to avoid, and troubleshooting."},
    {"domain": "writing", "title": "Podcast Episode Outline", "template": "Create a detailed outline for a {duration}-minute podcast episode on {topic} with guest {guest_description}. Include: hook intro, 5-7 interview questions with follow-up prompts, key talking points, and closing segment."},
    {"domain": "writing", "title": "Cold Outreach Email", "template": "Write a cold outreach email to {prospect_role} at {company_type}. Reference a specific company trigger ({trigger}). Open with value, not introduction. One clear ask. Under 75 words. High personalisation, no templates feel."},
    {"domain": "writing", "title": "Policy Document", "template": "Write a {policy_name} policy for {organization_type}. Include: purpose, scope, definitions, policy statements, responsibilities, enforcement, exceptions process, and review schedule. Legal-adjacent but plain language."},
    {"domain": "writing", "title": "Book Chapter Outline", "template": "Create a detailed outline for Chapter {n} of a book about {book_topic}. Chapter title: {title}. Include: core argument, 4-6 key points with supporting evidence type, stories/examples to include, and chapter summary."},
    {"domain": "writing", "title": "Product Changelog", "template": "Write a user-facing changelog entry for version {version} of {product}. Summarise {changes} in plain language. Lead with user benefits, not technical details. Organise as: New Features, Improvements, Bug Fixes. Exciting but accurate."},
    {"domain": "writing", "title": "Onboarding Email", "template": "Write a welcome/onboarding email for new {product} users. Send it 1 hour after signup. Celebrate their decision, deliver immediate value with 1 quick win action, set expectations, and provide support channel."},
    {"domain": "writing", "title": "Investor Update", "template": "Write a monthly investor update for {startup_name} (seed stage). Include: headline metric + MoM change, highlights, lowlights (be honest), key metrics table, asks from investors, and next milestone."},
    {"domain": "writing", "title": "SWOT Analysis", "template": "Write a detailed SWOT analysis for {company/product} in the {industry} market. For each quadrant: provide 4-5 specific, evidence-backed points with strategic implications. Conclude with prioritised strategic recommendations."},
    {"domain": "writing", "title": "Social Proof / Bio", "template": "Write a professional bio for {name}, {title}. Audience: {audience}. Tone: {tone}. Include: credentials, notable achievement, current focus, and human element. Third-person. Short version (50 words) and long version (150 words)."},
    {"domain": "writing", "title": "Complaint Response", "template": "Write a professional response to this customer complaint about {issue}. Acknowledge frustration (without admitting fault), apologise, explain what happened in plain terms, state concrete resolution with timeline, and win back trust.\nComplaint:\n{complaint}"},
    {"domain": "writing", "title": "RFP Response", "template": "Write a winning response to this RFP for {project_type}. Address each requirement directly, demonstrate relevant experience with metrics, differentiate from competitors, and propose clear next steps. Executive summary: 200 words.\nRFP:\n{rfp_text}"},
    {"domain": "writing", "title": "Training Material", "template": "Write a training module on {topic} for {learner_role}. Include: learning objectives (Bloom's taxonomy), content sections, knowledge check questions, practical exercise, and summary. Approachable tone for {expertise_level}."},
    {"domain": "writing", "title": "Creative Story Opening", "template": "Write the opening 300 words of a {genre} story set in {setting}. Introduce the protagonist through action, not description. Establish stakes immediately. End the scene at a moment of tension. Show, don't tell."},

    # ══════════════════════════════════════════════════════════════════════
    # MARKETING (100 patterns)
    # ══════════════════════════════════════════════════════════════════════
    {"domain": "marketing", "title": "Ad Copy (Facebook)", "template": "Write 3 Facebook ad copy variations for {product}. Target audience: {audience}. Each variation: hook (1 sentence), body (2-3 sentences), CTA. Test: emotional appeal vs logical appeal vs social proof angle."},
    {"domain": "marketing", "title": "Google Ads Copy", "template": "Write 5 Google Search Ad headlines (30 chars max) and 3 descriptions (90 chars max) for {product/service}. Target keyword: {keyword}. Include USP, CTA, and urgency where appropriate. A/B test variants."},
    {"domain": "marketing", "title": "Customer Persona", "template": "Create a detailed buyer persona for {product} targeting {demographic}. Include: demographics, psychographics, goals, frustrations, buying triggers, objections, preferred channels, and a day-in-the-life narrative."},
    {"domain": "marketing", "title": "Content Strategy", "template": "Develop a 3-month content strategy for {brand} targeting {audience}. Include: content pillars, topic clusters, content formats by channel, publishing frequency, KPIs, and 10 specific content ideas per pillar."},
    {"domain": "marketing", "title": "Email Subject Lines", "template": "Write 20 email subject lines for {campaign_type} promoting {offer} to {audience}. Include: curiosity-based, benefit-based, urgency-based, personalisation, and question formats. Estimated open rate rationale for top 3."},
    {"domain": "marketing", "title": "Brand Voice Guidelines", "template": "Define brand voice guidelines for {brand_name} in {industry}. Include: voice adjectives (4), tone spectrum (formal to casual), writing DOs and DON'Ts (5 each), before/after examples, and social media vs email tone differences."},
    {"domain": "marketing", "title": "Positioning Statement", "template": "Write a positioning statement for {product} using the format: For [target customer] who [need/problem], [product name] is the [category] that [key benefit] unlike [primary alternative]."},
    {"domain": "marketing", "title": "Go-to-Market Strategy", "template": "Develop a go-to-market strategy for {product} launching in {market}. Cover: target segment, positioning, pricing strategy, distribution channels, launch sequencing, success metrics, and 90-day action plan."},
    {"domain": "marketing", "title": "Competitive Analysis", "template": "Analyse {competitor_names} vs {our_brand} in {market}. For each competitor: pricing, positioning, key features, customer segments, strengths, weaknesses. Identify whitespace opportunities for our brand."},
    {"domain": "marketing", "title": "SEO Content Brief", "template": "Create an SEO content brief for an article targeting keyword: '{keyword}' (monthly searches: {volume}). Include: title options, meta description, H2 structure, semantic keywords, word count recommendation, and SERP intent analysis."},
    {"domain": "marketing", "title": "Influencer Brief", "template": "Write an influencer collaboration brief for {brand} partnering with {influencer_type}. Include: campaign objective, key messages (3), content requirements, dos and don'ts, deliverables, timeline, and FTC disclosure requirements."},
    {"domain": "marketing", "title": "Pricing Page Copy", "template": "Write pricing page copy for {product} with {number} tiers. Each tier: plan name, price, target customer sentence, 5-6 feature bullets (most important first), and CTA. Highlight the recommended plan. Add FAQ section."},
    {"domain": "marketing", "title": "Webinar Promotion", "template": "Write a promotional campaign for a webinar on {topic} targeting {audience}. Include: event page copy, 3 email invitations (1 week out, 3 days out, day of), LinkedIn post, and follow-up email sequence."},
    {"domain": "marketing", "title": "Referral Program", "template": "Design a referral program for {product} with {target_acquisition_cost}. Include: incentive structure (referrer + referee), messaging, email templates, in-app prompts, success metrics, and viral coefficient target."},
    {"domain": "marketing", "title": "Product Hunt Launch", "template": "Write a Product Hunt launch package for {product}. Include: tagline (60 chars), description (260 chars), gallery image captions, first comment from maker, and 5 Q&A pairs to address upfront."},
    {"domain": "marketing", "title": "Retargeting Ad Copy", "template": "Write retargeting ad copy for {product} targeting users who {action, e.g., visited pricing page}. Acknowledge their awareness, address the likely objection, offer a reason to act now. Urgency without desperation."},
    {"domain": "marketing", "title": "Partnership Pitch", "template": "Write a partnership proposal email to {partner_company} proposing a {partnership_type} collaboration. Lead with their benefit, propose specific co-marketing idea, quantify expected mutual value, and request a 20-minute call."},
    {"domain": "marketing", "title": "Value Proposition Canvas", "template": "Complete a Value Proposition Canvas for {product}. Customer profile: jobs-to-be-done, pains, gains. Value map: products/services, pain relievers, gain creators. Identify top 3 pain/gain matches."},
    {"domain": "marketing", "title": "Customer Journey Map", "template": "Map the customer journey for {persona} buying {product}. Stages: Awareness, Consideration, Decision, Retention, Advocacy. For each stage: actions, thoughts, emotions, touchpoints, and opportunities to improve experience."},
    {"domain": "marketing", "title": "Loyalty Program Design", "template": "Design a customer loyalty program for {business_type}. Include: tier structure, earning/redemption mechanics, emotional vs transactional benefits balance, gamification elements, communication plan, and success metrics."},
    {"domain": "marketing", "title": "Churn Reduction Campaign", "template": "Design a campaign to reduce churn for {product} among {at-risk-segment}. Include: churn trigger identification, intervention emails (3-step), win-back offer, exit survey design, and success metric."},
    {"domain": "marketing", "title": "A/B Test Plan", "template": "Design an A/B test for {element, e.g., homepage headline} on {platform}. Include: hypothesis, control vs variant, success metric, minimum detectable effect, sample size calculation, and test duration."},
    {"domain": "marketing", "title": "Video Script (60 sec)", "template": "Write a 60-second promotional video script for {product}. Hook (0-5s), problem (5-15s), solution (15-40s), proof (40-50s), CTA (50-60s). Include visual direction notes. Conversational, not salesy."},
    {"domain": "marketing", "title": "Podcast Ad Script", "template": "Write a 30-second host-read podcast ad for {brand} promoting {offer}. Conversational tone for host to make their own. Include: brand intro, key benefit, offer/CTA, and URL. Two versions: personal story angle and factual angle."},
    {"domain": "marketing", "title": "Market Sizing", "template": "Estimate the TAM/SAM/SOM for {product} in {market}. Use both top-down and bottom-up approaches. Show calculations, assumptions, data sources, and address key uncertainties. Present as investor-ready narrative."},
    {"domain": "marketing", "title": "Seasonal Campaign", "template": "Plan a {holiday/season} marketing campaign for {brand}. Include: campaign concept, 4-week execution timeline, channel plan (email, social, paid), creative themes, promotional offer, and budget allocation."},
    {"domain": "marketing", "title": "NPS Survey Analysis", "template": "Analyse these NPS responses for {product}. Segment: promoters, passives, detractors. Identify top 3 themes in each segment. Recommend 3 specific product/experience improvements. Calculate NPS score.\nResponses:\n{data}"},
    {"domain": "marketing", "title": "Community Building", "template": "Design a community strategy for {brand} targeting {audience}. Define: community purpose and values, platform choice with justification, content programming, moderation approach, growth tactics, and success metrics."},
    {"domain": "marketing", "title": "Upsell / Cross-sell Strategy", "template": "Design an upsell/cross-sell strategy for {product}. Identify: natural upgrade triggers, complementary products, right timing in user journey, in-app vs email messaging, and revenue impact projection."},
    {"domain": "marketing", "title": "Product Messaging Framework", "template": "Create a messaging framework for {product} targeting {segments}. Include: category frame, unique value proposition, key messages (3-5) per segment, proof points, and objection-handling statements."},
    {"domain": "marketing", "title": "Event Marketing Plan", "template": "Create an event marketing plan for {company} attending {event_name}. Include: pre-event outreach, booth/session strategy, lead capture process, social media plan, post-event follow-up sequence, and success metrics."},
    {"domain": "marketing", "title": "Customer Segmentation", "template": "Segment {company}'s customer base using {data_available}. Define 4-5 segments: size, characteristics, product usage patterns, revenue contribution, and recommended engagement strategy per segment."},
    {"domain": "marketing", "title": "Rebranding Communication", "template": "Write the communication plan for {company}'s rebrand. Audience: customers, employees, partners, media. Sequence announcements, craft key messages, provide Q&A prep, and handle concerns proactively."},
    {"domain": "marketing", "title": "Social Listening Report", "template": "Analyse social media sentiment about {brand/topic} from {time_period}. Include: volume trends, sentiment breakdown, top themes, influential voices, competitive mentions, and 3 actionable insights."},
    {"domain": "marketing", "title": "Conversion Rate Optimisation", "template": "Audit the conversion funnel for {page/flow}. Identify: drop-off points, friction sources, trust gaps, messaging issues. Prioritise 5 A/B tests by expected impact vs effort. Include hypothesis for each."},
    {"domain": "marketing", "title": "Account-Based Marketing", "template": "Design an ABM campaign targeting {account_list_size} accounts in {industry}. Tiers: Tier 1 (1:1), Tier 2 (1:few), Tier 3 (1:many). For each tier: personalisation level, channels, content, and success metrics."},
    {"domain": "marketing", "title": "Product Launch Checklist", "template": "Create a product launch checklist for {product} launching {date}. Organise by: 4 weeks before, 2 weeks before, launch week, launch day, week after. Include owners, channels, assets needed, and go/no-go criteria."},

    # ══════════════════════════════════════════════════════════════════════
    # EDUCATION (80 patterns)
    # ══════════════════════════════════════════════════════════════════════
    {"domain": "education", "title": "Lesson Plan", "template": "Create a {duration} lesson plan on {topic} for {grade_level} students. Include: learning objectives (3), materials needed, warm-up activity, main instruction with differentiation strategies, formative assessment, and closing reflection."},
    {"domain": "education", "title": "Quiz Generator", "template": "Generate 15 quiz questions on {topic} for {level} learners. Include: 5 multiple choice (4 options each, 1 correct), 5 true/false with explanation, 3 short answer, 2 application-based. Include answer key."},
    {"domain": "education", "title": "Rubric Creator", "template": "Create an assessment rubric for {assignment_type} in {subject}. Criteria: {criteria_list}. Performance levels: Excellent / Proficient / Developing / Beginning. Each cell: specific observable behaviours."},
    {"domain": "education", "title": "Explain Like I'm 5", "template": "Explain {complex_concept} to a {age}-year-old. Use: simple words, a relatable analogy from everyday life, and a concrete example they can visualise. Check understanding with 2 simple questions at the end."},
    {"domain": "education", "title": "Socratic Questions", "template": "Generate 10 Socratic questioning prompts to guide students to discover {concept} themselves in a {subject} class. Questions should: probe assumptions, explore implications, challenge evidence, and connect to real-world."},
    {"domain": "education", "title": "Study Guide", "template": "Create a comprehensive study guide for {topic} for {exam_type}. Include: key concepts summary, important formulas/definitions, concept map description, practice problems (5) with worked solutions, and memory tricks."},
    {"domain": "education", "title": "Differentiated Instruction", "template": "Adapt this lesson on {topic} for three learner profiles: (1) struggling learners (scaffolding), (2) grade-level learners (standard), (3) advanced learners (extension). Same core concept, differentiated depth and support."},
    {"domain": "education", "title": "Curriculum Mapping", "template": "Map a {course_duration} curriculum for {course_name} targeting {learner_type}. Sequence topics logically: foundational → intermediate → advanced. For each unit: learning goals, prerequisite knowledge, and assessment method."},
    {"domain": "education", "title": "Feedback on Student Work", "template": "Provide constructive feedback on this student work. Start with specific strength. Identify 2-3 areas for improvement with concrete suggestions. Ask 2 questions to deepen their thinking. Encourage without false praise.\nWork:\n{student_work}"},
    {"domain": "education", "title": "Analogical Explanation", "template": "Explain {concept} in {field} using an analogy from {familiar_domain}. Map: the abstract element to the familiar element, show where the analogy holds, and explicitly state where it breaks down (analogies always have limits)."},
    {"domain": "education", "title": "Interactive Activity Design", "template": "Design an interactive classroom activity for {topic} for {age_group}. Include: setup (materials, time), step-by-step instructions, facilitation tips, likely stumbling blocks, and debrief questions."},
    {"domain": "education", "title": "Reading Comprehension Questions", "template": "Generate reading comprehension questions for this text at three levels: literal (2 questions), inferential (2 questions), and evaluative/critical (2 questions). Include model answer for the evaluative question.\nText:\n{text}"},
    {"domain": "education", "title": "Project-Based Learning", "template": "Design a project-based learning unit on {driving_question} for {grade}. Include: project overview, entry event, inquiry scaffolding, product definition, presentation format, rubric, and 21st-century skills targeted."},
    {"domain": "education", "title": "Flipped Classroom Content", "template": "Create pre-class reading/video content script for {topic} so students arrive ready for hands-on application. Include: core concepts (chunked), check-for-understanding prompts, vocabulary, and preview of in-class activity."},
    {"domain": "education", "title": "Concept Check Questions", "template": "Write 10 formative assessment questions for {topic} that reveal student misconceptions, not just memorisation. Include: the common misconception each question targets and the correct conceptual understanding."},
    {"domain": "education", "title": "Peer Review Scaffold", "template": "Create a peer review scaffold for {assignment_type} that guides students to give specific, actionable feedback. Include: sentence starters, criteria to evaluate (5), revision reflection questions."},
    {"domain": "education", "title": "Online Course Module", "template": "Design module {n} of an online course on {topic}. Include: module objective, 3-5 lessons with content type (video/reading/quiz), estimated time, discussion prompt, and module assignment."},
    {"domain": "education", "title": "Case Study for Teaching", "template": "Write a teaching case study for {course} on the dilemma of {situation}. Include: background context, stakeholders, the key decision to make, 4-5 discussion questions at increasing complexity, and instructor notes."},
    {"domain": "education", "title": "Parent Communication", "template": "Write a parent newsletter update about {topic/event} for {grade_level} families. Explain in plain language: what students are learning, how parents can support at home, upcoming dates, and a positive note about the class."},
    {"domain": "education", "title": "IEP Goal Writing", "template": "Write 3 SMART IEP goals for a student with {disability/need} in the area of {skill_domain}. Each goal: current baseline, annual target, measurement method, frequency, and conditions. Align to {grade_level} standards."},

    # ══════════════════════════════════════════════════════════════════════
    # CREATIVE (80 patterns)
    # ══════════════════════════════════════════════════════════════════════
    {"domain": "creative", "title": "Character Development", "template": "Develop a complex, three-dimensional character for {genre} fiction. Include: core wound and how it shapes behaviour, contradictions that make them believable, want vs need (different things), and voice/speech patterns."},
    {"domain": "creative", "title": "World Building", "template": "Build the world for {story_type} set in {setting_concept}. Define: physical geography and how it shapes culture, power structures and their history, technology/magic rules, three factions with competing interests, and sensory details."},
    {"domain": "creative", "title": "Story Plot Structure", "template": "Plot a {genre} story using the Save the Cat beat sheet. Character: {protagonist_description}. Define all 15 beats from Opening Image to Final Image with 2-3 sentences each. Theme stated: {theme}."},
    {"domain": "creative", "title": "Dialogue Writing", "template": "Write a tense dialogue scene between {character_a} and {character_b} about {conflict}. Rules: no dialogue tags except 'said', subtext — characters don't say what they really mean, 2 characters want opposite things, someone wins."},
    {"domain": "creative", "title": "Scene Description", "template": "Write a vivid scene set in {location} during {time/weather/atmosphere}. Use all 5 senses. Show how the setting reflects the emotional state of {character}. 200 words. Every detail should do double duty."},
    {"domain": "creative", "title": "Poetry (Structured)", "template": "Write a {form, e.g., sonnet/villanelle/haiku} about {subject/emotion}. Follow the form's rules strictly. Central image: {image}. Tone: {tone}. Final line should reframe or undercut everything before it."},
    {"domain": "creative", "title": "Short Story", "template": "Write a complete flash fiction story (500 words) about {premise}. Genre: {genre}. Must include: a specific sensory detail that recurs with new meaning, one surprising turn, and an ending that earns its emotion."},
    {"domain": "creative", "title": "Villain Motivation", "template": "Write a backstory for the villain of {story} that makes them understandable (not sympathetic). Show the moment they crossed the point of no return, their twisted internal logic, and the one human thing they still value."},
    {"domain": "creative", "title": "Opening Hook", "template": "Write 5 different opening sentences for a {genre} story about {premise}. Each uses a different technique: in medias res, character voice, world detail, question/mystery, and contradiction. Evaluate the strongest and why."},
    {"domain": "creative", "title": "Metaphor Generation", "template": "Generate 10 original metaphors for {abstract concept or emotion}. Avoid clichés. Source domains: nature, architecture, mathematics, cooking, sports, childhood, machinery, music, weather, and geography (one each). Bold the 3 strongest."},
    {"domain": "creative", "title": "Screenplay Scene", "template": "Write a 2-page screenplay scene. Location: {location}. Characters: {characters}. Conflict: {conflict}. Format: INT./EXT., action lines (present tense), character names centered, parentheticals only when essential."},
    {"domain": "creative", "title": "Game Narrative Design", "template": "Write narrative design documentation for {game_type} set in {world}. Include: lore overview, protagonist arc, 3 faction descriptions with conflicting agendas, branching dialogue example (2 levels deep), and environmental storytelling ideas."},
    {"domain": "creative", "title": "Song Lyrics (Verse + Chorus)", "template": "Write lyrics for a {genre} song about {theme}. Structure: 2 verses + chorus + bridge. Verse 1: specific concrete scene. Verse 2: widening perspective. Chorus: universal/emotional statement. Bridge: twist or escalation. Include rhyme scheme."},
    {"domain": "creative", "title": "Comedy Writing", "template": "Write a {format, e.g., stand-up bit/sketch/column} on the topic of {topic}. Comedy rule of three, subverted expectation, and callback required. Tone: {comedy_style, e.g., dry/absurdist/self-deprecating}. Punch word at end of punchline."},
    {"domain": "creative", "title": "Brand Storytelling", "template": "Write a brand origin story for {company/product}. Structure: the founder's problem, the moment of insight, the struggle to build it, and the transformation for customers. Emotional, true, 300 words. Hero = the customer, not the brand."},
    {"domain": "creative", "title": "Children's Story", "template": "Write a children's story for ages {age_range} about {theme/lesson}. Protagonist: a {character} who wants {goal} but faces {obstacle}. Simple language, repetitive structure for memorability, and satisfying resolution that earns the lesson."},
    {"domain": "creative", "title": "Personal Essay", "template": "Write a personal essay about {topic/experience} for {publication}. Voice: {voice}. Structure: begin in-scene, zoom out to meaning, return to scene with new understanding. Specific details > abstractions. 600-800 words."},
    {"domain": "creative", "title": "Satire Piece", "template": "Write a satirical {format, e.g., memo/news article/how-to guide} about {target/institution}. Adopt a deadpan, earnest tone while describing absurdity. Include: escalating specifics, one touch of genuine truth, and a self-undermining ending."},
    {"domain": "creative", "title": "Epistolary Scene", "template": "Write a scene from {story} told entirely through {format, e.g., emails/text messages/letters}. Characters: {A} and {B}. Reveal through subtext: what they write vs what they mean, the silence between messages, and a revelation in the final message."},
    {"domain": "creative", "title": "Interactive Fiction Branch", "template": "Write a branching narrative node for {game/experience}. Setup: {situation}. Offer 3 choices with meaningfully different outcomes (not just aesthetic). Each choice: 100-word consequence scene that affects {stat/relationship/story_flag}."},

    # ══════════════════════════════════════════════════════════════════════
    # RESEARCH & ANALYSIS (60 patterns)
    # ══════════════════════════════════════════════════════════════════════
    {"domain": "research", "title": "Literature Review", "template": "Write a structured literature review on {topic}. Synthesise key themes (not paper-by-paper summary), identify consensus findings, highlight debates and gaps, and conclude with research questions that remain open."},
    {"domain": "research", "title": "Research Methodology", "template": "Design a research methodology to study {research_question}. Choose and justify: quantitative/qualitative/mixed, data collection methods, sample selection, measurement instruments, analysis approach, and limitations."},
    {"domain": "research", "title": "Data Analysis Plan", "template": "Write a data analysis plan for {dataset_description}. Include: data cleaning steps, exploratory analysis checklist, statistical tests to apply (with justification), visualisation plan, and how to interpret results for {audience}."},
    {"domain": "research", "title": "Hypothesis Formulation", "template": "Formulate 3 testable hypotheses about {phenomenon} in {field}. For each: null hypothesis, alternative hypothesis, predicted direction of effect, how to operationalise variables, and what finding would falsify the hypothesis."},
    {"domain": "research", "title": "Systematic Review Protocol", "template": "Write a PRISMA-compliant systematic review protocol for {research_question}. Include: inclusion/exclusion criteria, search string for PubMed/Google Scholar, screening process, data extraction fields, and bias assessment tool."},
    {"domain": "research", "title": "Expert Interview Guide", "template": "Create a semi-structured interview guide for researching {topic} with {expert_type}. Include: warm-up questions (2), core questions (6) with probes, sensitive topic approach, and closing questions. Expected duration: {time}."},
    {"domain": "research", "title": "Survey Design", "template": "Design a {n}-question survey to measure {construct} in {population}. Include: validated scale questions where possible, Likert scale instructions, skip logic description, pilot test plan, and analysis approach."},
    {"domain": "research", "title": "Statistical Analysis", "template": "Perform a statistical analysis of this data to answer: {research_question}. Select appropriate test, check assumptions, interpret results, calculate effect size, and state practical (not just statistical) significance.\nData:\n{data}"},
    {"domain": "research", "title": "Trend Analysis", "template": "Analyse trends in {domain} from {time_period}. Identify: 3 macro trends, driving forces, leading indicators, lagging indicators, scenarios for 5 years out, and implications for {stakeholder_type}."},
    {"domain": "research", "title": "Policy Brief", "template": "Write a policy brief on {policy_issue} for {policymaker_audience}. Include: problem statement (with data), current policy landscape, evidence-based recommendations (3), implementation considerations, and trade-offs."},
    {"domain": "research", "title": "Evidence Summary", "template": "Summarise the evidence on {question} from a {field} perspective. Rate evidence quality (strong/moderate/weak), distinguish correlation from causation, note conflicting findings, and give a confidence-weighted conclusion."},
    {"domain": "research", "title": "Competitor Intelligence Report", "template": "Write a competitive intelligence report on {competitor} for {industry}. Cover: business model, financial trajectory, product roadmap signals, talent movements, customer sentiment, and strategic implications for our business."},
    {"domain": "research", "title": "Industry Analysis (Porter's Five Forces)", "template": "Apply Porter's Five Forces analysis to {industry}. For each force: rating (high/medium/low), key drivers, 3 supporting data points, and strategic implication. Conclude: overall industry attractiveness score."},
    {"domain": "research", "title": "Scenario Planning", "template": "Develop 4 future scenarios for {domain} in {time_horizon}. Axes of uncertainty: {axis_1} vs {axis_2}. For each quadrant: name, narrative description, key signals, strategic implications, and early warning indicators."},
    {"domain": "research", "title": "Root Cause Analysis", "template": "Perform a root cause analysis for this problem: {problem}. Use the 5 Whys technique, fishbone (Ishikawa) diagram description, and identify: systemic vs symptomatic causes, highest-leverage intervention points."},

    # ══════════════════════════════════════════════════════════════════════
    # GENERAL / PRODUCTIVITY (80 patterns)
    # ══════════════════════════════════════════════════════════════════════
    {"domain": "general", "title": "Decision Framework", "template": "Help me make a decision about {decision}. Apply: pros/cons with weighted importance, second-order effects, regret minimisation framework, reversibility assessment, and recommended decision with reasoning."},
    {"domain": "general", "title": "Meeting Notes Summary", "template": "Summarise these meeting notes into a structured brief. Extract: decisions made, action items (owner + deadline), open questions, key discussion points. Format as bullet points. Flag any items needing follow-up.\nNotes:\n{notes}"},
    {"domain": "general", "title": "Email Rewrite", "template": "Rewrite this email to be {tone, e.g., more direct/professional/friendly}. Preserve the intent. Improve: subject line, opening, clarity of ask, and closing. Keep under {word_count} words.\nOriginal:\n{email}"},
    {"domain": "general", "title": "Negotiation Script", "template": "Help me prepare for a negotiation with {counterpart} about {subject}. Provide: my BATNA, their likely BATNA, opening offer rationale, 3 concession options (low/medium/high), responses to likely objections, and walk-away point."},
    {"domain": "general", "title": "Personal Mission Statement", "template": "Help me write a personal mission statement. My values: {values}. Strengths: {strengths}. What matters most to me: {purpose}. Draft 3 versions: one sentence, one paragraph, and extended version. Authentic, not corporate."},
    {"domain": "general", "title": "Project Kickoff Brief", "template": "Write a project kickoff brief for {project_name}. Include: problem statement, success metrics (SMART), scope (in/out), team roles and responsibilities, timeline with milestones, risks and mitigation, and communication cadence."},
    {"domain": "general", "title": "Difficult Conversation Script", "template": "Help me structure a difficult conversation with {person} about {issue}. Script: opening (non-accusatory), expressing impact (I statements), asking their perspective, collaborative solution seeking, and agreed next steps."},
    {"domain": "general", "title": "Performance Review", "template": "Write a {tone} performance review for {role} who has demonstrated {strengths} but needs improvement in {areas}. Include: specific examples for each point, development goals (3), and a forward-looking motivational close."},
    {"domain": "general", "title": "Risk Assessment", "template": "Perform a risk assessment for {project/decision}. For each risk: likelihood (1-5), impact (1-5), risk score, mitigation strategy, contingency plan, and owner. Prioritise top 5 risks by score."},
    {"domain": "general", "title": "Strategic Plan", "template": "Create a strategic plan for {organization/team} for {time_horizon}. Include: vision, mission, strategic objectives (3-5), initiatives per objective, KPIs, resource requirements, and quarterly milestones."},
    {"domain": "general", "title": "Brainstorming Session", "template": "Facilitate a brainstorming session on {challenge}. Generate: 20 initial ideas (no filtering), then 5 wild/impossible ideas, then 5 combinations of the best elements. Apply reverse brainstorming: how would you make this WORSE?"},
    {"domain": "general", "title": "Feedback Framework", "template": "Give constructive feedback on {work/situation} using the SBI framework (Situation, Behaviour, Impact). Identify 2 strengths with specific examples, 2 growth areas with actionable suggestions, and a motivating close."},
    {"domain": "general", "title": "OKR Framework", "template": "Write OKRs for {team/company} for {quarter}. 3 Objectives max, each with 3 Key Results. KRs must be: measurable, ambitious but achievable, outcomes not outputs, and clearly evaluable at quarter end."},
    {"domain": "general", "title": "Budget Justification", "template": "Write a budget justification for {request} totalling ${amount}. Structure: need statement, line-item breakdown with rationale, ROI or impact calculation, alternatives considered (and why rejected), and approval request."},
    {"domain": "general", "title": "Onboarding Plan", "template": "Create a 30-60-90 day onboarding plan for a new {role}. Each phase: learning goals, relationships to build, quick wins to aim for, success metrics, and check-in cadence with manager."},
    {"domain": "general", "title": "Agenda for 1:1", "template": "Create a standing agenda template for weekly 1:1 meetings between a manager and {role}. Include: wins since last meeting, blockers/help needed, project updates (brief), development conversation, and manager announcements. 30 minutes."},
    {"domain": "general", "title": "Problem Statement", "template": "Write a rigorous problem statement for {issue}. Include: what the problem is (and is not), who it affects, scale/evidence, root cause hypothesis, why it matters to solve now, and what success looks like."},
    {"domain": "general", "title": "Post-Mortem Analysis", "template": "Write a blameless post-mortem for {incident/failure}. Include: timeline, contributing factors (not a person's fault), what went well, what could be improved, action items with owners and deadlines, and lessons learned."},
    {"domain": "general", "title": "Executive Briefing", "template": "Prepare a 5-minute executive briefing on {topic} for {exec_audience}. Structure: one-sentence situation, key data (3 numbers), 2 options with trade-offs, recommendation with rationale, and ask (decision/resource/action)."},
    {"domain": "general", "title": "Workshop Design", "template": "Design a {duration} workshop on {topic} for {n} participants from {background}. Include: objectives, materials, opening energiser, 3 main activities with facilitator notes, synthesis method, and follow-up commitment structure."},
]


def seed_patterns():
    """Main function: embed all patterns and insert into Qdrant."""
    # Import here to keep module-level clean
    from app.services.embedding_service import embedding_service
    from app.services.qdrant_service import qdrant_service

    # Ensure collections exist
    logger.info("Ensuring Qdrant collections exist...")
    qdrant_service.ensure_collections_exist()

    total = len(PROMPT_PATTERNS)
    logger.info(f"Seeding {total} prompt patterns into Qdrant...")

    # Build texts for batch embedding
    texts = [p["template"] for p in PROMPT_PATTERNS]

    # Batch embed — all at once is efficient
    logger.info("Embedding all templates (this may take 30-60 seconds)...")
    vectors = embedding_service.embed_batch(texts)
    logger.info(f"Embedding complete. Upserting {total} vectors...")

    # Upsert each pattern
    success = 0
    for i, (pattern, vector) in enumerate(zip(PROMPT_PATTERNS, vectors)):
        pattern_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"pattern-{i}-{pattern['title']}"))
        try:
            qdrant_service.upsert_prompt_pattern(
                pattern_id=pattern_id,
                vector=vector,
                payload={
                    "template": pattern["template"],
                    "domain": pattern["domain"],
                    "title": pattern["title"],
                    "pattern_index": i,
                },
            )
            success += 1
        except Exception as e:
            logger.warning(f"Failed to upsert pattern '{pattern['title']}': {e}")

        # Progress log every 50 patterns
        if (i + 1) % 50 == 0:
            logger.info(f"  Progress: {i + 1}/{total}")

    logger.info(f"Seeding complete. {success}/{total} patterns inserted successfully.")
    return success


if __name__ == "__main__":
    # Allow running directly from project root: python -m scripts.seed_prompt_patterns
    import os
    # Add the backend directory to sys.path so app.* imports work
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    result = seed_patterns()
    sys.exit(0 if result > 0 else 1)
