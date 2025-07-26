"""
AI Report Generator Service
Uses OpenRouter for multi-model LLM calls with fallback mechanisms
"""

import asyncio
import logging
from typing import Dict, Any, List
from services.openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)

class AIReportGenerator:
    """
    AI-powered report generator using OpenRouter multi-model approach
    """
    
    def __init__(self):
        self.client = get_openrouter_client()
        
        # Model assignments (will be used for debate system later)
        self.primary_model = "anthropic/claude-3-5-sonnet-20241022"
        self.secondary_model = "openai/gpt-4o"
        self.judge_model = "google/gemini-pro-1.5"
    
    async def generate_business_plan(
        self, 
        data: Dict[str, Any], 
        additional_context: str = ""
    ) -> str:
        """
        Generate comprehensive business plan using OpenRouter
        """
        
        prompt = self._create_business_plan_prompt(data, additional_context)
        
        try:
            response = await self.client.chat_completion(
                model=self.primary_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert business analyst specializing in creating comprehensive business plans."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2048,
                temperature=0.7
            )
            
            logger.info(f"Business plan generated successfully using {self.primary_model}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate business plan: {e}")
            raise
    
    async def generate_market_analysis(
        self, 
        data: Dict[str, Any], 
        additional_context: str = ""
    ) -> str:
        """
        Generate market analysis report using OpenRouter
        """
        
        prompt = self._create_market_analysis_prompt(data, additional_context)
        
        try:
            response = await self.client.chat_completion(
                model=self.secondary_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a market research expert with deep knowledge of industry trends and competitive analysis."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2048,
                temperature=0.6
            )
            
            logger.info(f"Market analysis generated successfully using {self.secondary_model}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate market analysis: {e}")
            raise
    
    async def generate_investment_summary(
        self, 
        data: Dict[str, Any], 
        additional_context: str = ""
    ) -> str:
        """
        Generate investment summary using OpenRouter
        """
        
        prompt = self._create_investment_summary_prompt(data, additional_context)
        
        try:
            response = await self.client.chat_completion(
                model=self.judge_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a seasoned investment advisor with expertise in evaluating business opportunities and financial projections."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2048,
                temperature=0.5
            )
            
            logger.info(f"Investment summary generated successfully using {self.judge_model}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate investment summary: {e}")
            raise
    
    async def generate_financial_analysis(
        self, 
        data: Dict[str, Any], 
        additional_context: str = ""
    ) -> str:
        """
        Generate comprehensive financial analysis report
        """
        
        prompt = self._create_financial_analysis_prompt(data, additional_context)
        
        try:
            response = await self.client.chat_completion(
                model=self.primary_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a financial analyst expert specializing in data-driven financial insights, ratio analysis, and performance evaluation."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2048,
                temperature=0.6
            )
            
            logger.info(f"Financial analysis generated successfully using {self.primary_model}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate financial analysis: {e}")
            raise
    
    async def generate_risk_assessment(
        self, 
        data: Dict[str, Any], 
        additional_context: str = ""
    ) -> str:
        """
        Generate risk assessment and mitigation strategies
        """
        
        prompt = self._create_risk_assessment_prompt(data, additional_context)
        
        try:
            response = await self.client.chat_completion(
                model=self.secondary_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a risk management specialist with expertise in identifying, analyzing, and mitigating business risks across various industries."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2048,
                temperature=0.7
            )
            
            logger.info(f"Risk assessment generated successfully using {self.secondary_model}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate risk assessment: {e}")
            raise
    
    async def generate_competitive_analysis(
        self, 
        data: Dict[str, Any], 
        additional_context: str = ""
    ) -> str:
        """
        Generate competitive landscape analysis
        """
        
        prompt = self._create_competitive_analysis_prompt(data, additional_context)
        
        try:
            response = await self.client.chat_completion(
                model=self.judge_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a strategic business analyst specializing in competitive intelligence, market positioning, and strategic planning."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2048,
                temperature=0.6
            )
            
            logger.info(f"Competitive analysis generated successfully using {self.judge_model}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate competitive analysis: {e}")
            raise
    
    async def generate_data_insights(
        self, 
        data: Dict[str, Any], 
        additional_context: str = ""
    ) -> str:
        """
        Generate data-driven insights and recommendations
        """
        
        prompt = self._create_data_insights_prompt(data, additional_context)
        
        try:
            response = await self.client.chat_completion(
                model=self.primary_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a data scientist and business intelligence expert specializing in extracting actionable insights from complex datasets."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2048,
                temperature=0.5
            )
            
            logger.info(f"Data insights generated successfully using {self.primary_model}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate data insights: {e}")
            raise
    
    async def quick_analysis(self, data: Dict[str, Any]) -> str:
        """
        Generate quick analysis summary for fast preview
        """
        
        prompt = self._create_quick_analysis_prompt(data)
        
        try:
            response = await self.client.chat_completion(
                model=self.secondary_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a business analyst providing quick, concise insights from data. Focus on key findings and immediate actionable recommendations."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=1024,
                temperature=0.7
            )
            
            logger.info(f"Quick analysis generated successfully using {self.secondary_model}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate quick analysis: {e}")
            raise
    
    def _create_business_plan_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Create business plan generation prompt"""
        
        return f"""
Based on the provided data and context, create a comprehensive business plan including:

1. Executive Summary
2. Business Description
3. Market Analysis
4. Organization & Management
5. Service/Product Line
6. Marketing & Sales Strategy
7. Financial Projections
8. Risk Analysis

Data provided:
{data}

Additional context:
{context}

Please provide a detailed, professional business plan that addresses all these sections.
"""
    
    def _create_market_analysis_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Create market analysis prompt"""
        
        return f"""
Conduct a thorough market analysis based on the provided data, including:

1. Market Size & Growth Potential
2. Target Market Segmentation
3. Competitive Landscape
4. Industry Trends
5. Market Entry Strategy
6. SWOT Analysis
7. Market Opportunities & Threats

Data provided:
{data}

Additional context:
{context}

Provide actionable insights and data-driven recommendations.
"""
    
    def _create_investment_summary_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Create investment summary prompt"""
        
        return f"""
Create an investment summary and recommendation based on the provided data:

1. Investment Opportunity Overview
2. Financial Highlights
3. Key Success Factors
4. Risk Assessment
5. Return on Investment Analysis
6. Investment Recommendation
7. Exit Strategy Considerations

Data provided:
{data}

Additional context:
{context}

Provide a clear investment recommendation with supporting rationale.
"""
    
    def _create_financial_analysis_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Create financial analysis prompt"""
        
        return f"""
Conduct a comprehensive financial analysis based on the provided data:

1. Financial Performance Overview
2. Key Financial Ratios Analysis
   - Liquidity ratios
   - Profitability ratios
   - Efficiency ratios
   - Leverage ratios
3. Trend Analysis
4. Cash Flow Analysis
5. Financial Strengths & Weaknesses
6. Performance Benchmarking
7. Financial Recommendations
8. Future Financial Projections

Data provided:
{data}

Additional context:
{context}

Provide detailed financial insights with supporting calculations and recommendations.
"""
    
    def _create_risk_assessment_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Create risk assessment prompt"""
        
        return f"""
Perform a comprehensive risk assessment based on the provided data:

1. Risk Identification
   - Market risks
   - Operational risks
   - Financial risks
   - Strategic risks
   - Regulatory risks
2. Risk Analysis & Quantification
3. Risk Impact Assessment
4. Risk Probability Evaluation
5. Risk Prioritization Matrix
6. Risk Mitigation Strategies
7. Risk Monitoring Framework
8. Contingency Planning

Data provided:
{data}

Additional context:
{context}

Provide actionable risk management recommendations with specific mitigation strategies.
"""
    
    def _create_competitive_analysis_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Create competitive analysis prompt"""
        
        return f"""
Conduct a thorough competitive analysis based on the provided data:

1. Competitive Landscape Overview
2. Key Competitors Identification
3. Competitive Positioning Analysis
4. Market Share Analysis
5. Competitive Advantages & Disadvantages
6. SWOT Analysis vs Competitors
7. Competitive Strategies Assessment
8. Market Differentiation Opportunities
9. Competitive Response Strategies
10. Strategic Recommendations

Data provided:
{data}

Additional context:
{context}

Provide strategic insights for competitive advantage and market positioning.
"""
    
    def _create_data_insights_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Create data insights prompt"""
        
        return f"""
Extract meaningful insights and patterns from the provided data:

1. Data Summary & Overview
2. Key Patterns & Trends Identification
3. Statistical Analysis
4. Correlation Analysis
5. Anomaly Detection
6. Predictive Insights
7. Business Intelligence Findings
8. Data-Driven Recommendations
9. Actionable Next Steps
10. Data Quality Assessment

Data provided:
{data}

Additional context:
{context}

Focus on extracting actionable business insights that can drive decision-making.
"""
    
    def _create_quick_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create quick analysis prompt"""
        
        return f"""
Provide a quick analysis of the provided data with focus on:

1. Key Findings (top 3-5 insights)
2. Critical Issues or Opportunities
3. Immediate Recommendations
4. Next Steps

Data provided:
{data}

Keep the analysis concise but actionable. Focus on the most important insights that require immediate attention.
"""
    
    async def test_models(self) -> Dict[str, bool]:
        """Test all configured models"""
        
        test_prompt = "Respond with 'Model test successful' if you can understand this message."
        
        results = {}
        
        for model_name, model_id in [
            ("primary", self.primary_model),
            ("secondary", self.secondary_model), 
            ("judge", self.judge_model)
        ]:
            try:
                response = await self.client.chat_completion(
                    model=model_id,
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=50,
                    temperature=0.1
                )
                results[model_name] = "successful" in response.lower()
                logger.info(f"Model {model_name} ({model_id}) test: {'PASS' if results[model_name] else 'FAIL'}")
                
            except Exception as e:
                results[model_name] = False
                logger.error(f"Model {model_name} ({model_id}) test failed: {e}")
        
        return results
