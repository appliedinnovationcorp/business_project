from typing import Dict, List, Any
import json

class WorkflowTemplateManager:
    """Manages industry-specific workflow templates"""
    
    @staticmethod
    def get_healthcare_templates() -> List[Dict[str, Any]]:
        """Healthcare industry workflow templates"""
        return [
            {
                "name": "Medical Document Analysis",
                "description": "Automated analysis of medical documents for key information extraction",
                "category": "healthcare",
                "tags": ["medical", "document-analysis", "hipaa-compliant"],
                "nodes": [
                    {
                        "id": "start",
                        "type": "input",
                        "data": {"label": "Medical Document Input"},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "textract",
                        "type": "textract",
                        "data": {
                            "label": "Extract Text",
                            "config": {
                                "features": ["FORMS", "TABLES"],
                                "hipaa_compliant": True
                            }
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "medical_nlp",
                        "type": "comprehend_medical",
                        "data": {
                            "label": "Medical Entity Recognition",
                            "config": {
                                "detect_entities": True,
                                "detect_phi": True
                            }
                        },
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "compliance_check",
                        "type": "custom",
                        "data": {
                            "label": "HIPAA Compliance Check",
                            "config": {
                                "function": "hipaa_compliance_validator"
                            }
                        },
                        "position": {"x": 700, "y": 100}
                    },
                    {
                        "id": "output",
                        "type": "output",
                        "data": {"label": "Structured Medical Data"},
                        "position": {"x": 900, "y": 100}
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "start", "target": "textract"},
                    {"id": "e2", "source": "textract", "target": "medical_nlp"},
                    {"id": "e3", "source": "medical_nlp", "target": "compliance_check"},
                    {"id": "e4", "source": "compliance_check", "target": "output"}
                ]
            },
            {
                "name": "Patient Sentiment Analysis",
                "description": "Analyze patient feedback and reviews for sentiment and key insights",
                "category": "healthcare",
                "tags": ["sentiment", "patient-feedback", "quality-improvement"],
                "nodes": [
                    {
                        "id": "start",
                        "type": "input",
                        "data": {"label": "Patient Feedback"},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "sentiment",
                        "type": "comprehend",
                        "data": {
                            "label": "Sentiment Analysis",
                            "config": {"analysis_type": "sentiment"}
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "key_phrases",
                        "type": "comprehend",
                        "data": {
                            "label": "Key Phrase Extraction",
                            "config": {"analysis_type": "key_phrases"}
                        },
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "categorization",
                        "type": "custom",
                        "data": {
                            "label": "Healthcare Category Classification",
                            "config": {
                                "categories": ["care_quality", "staff_behavior", "facilities", "billing"]
                            }
                        },
                        "position": {"x": 700, "y": 100}
                    },
                    {
                        "id": "output",
                        "type": "output",
                        "data": {"label": "Patient Insights Report"},
                        "position": {"x": 900, "y": 100}
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "start", "target": "sentiment"},
                    {"id": "e2", "source": "start", "target": "key_phrases"},
                    {"id": "e3", "source": "sentiment", "target": "categorization"},
                    {"id": "e4", "source": "key_phrases", "target": "categorization"},
                    {"id": "e5", "source": "categorization", "target": "output"}
                ]
            }
        ]
    
    @staticmethod
    def get_manufacturing_templates() -> List[Dict[str, Any]]:
        """Manufacturing industry workflow templates"""
        return [
            {
                "name": "Quality Control Image Analysis",
                "description": "Automated visual inspection of manufactured products",
                "category": "manufacturing",
                "tags": ["quality-control", "computer-vision", "defect-detection"],
                "nodes": [
                    {
                        "id": "start",
                        "type": "input",
                        "data": {"label": "Product Images"},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "rekognition",
                        "type": "rekognition",
                        "data": {
                            "label": "Image Analysis",
                            "config": {
                                "detect_labels": True,
                                "detect_custom_labels": True,
                                "model_arn": "manufacturing_defects_model"
                            }
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "defect_classifier",
                        "type": "custom",
                        "data": {
                            "label": "Defect Classification",
                            "config": {
                                "defect_types": ["scratch", "dent", "discoloration", "misalignment"],
                                "severity_levels": ["minor", "major", "critical"]
                            }
                        },
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "quality_decision",
                        "type": "condition",
                        "data": {
                            "label": "Quality Gate",
                            "config": {
                                "condition": "defect_severity < 'major'"
                            }
                        },
                        "position": {"x": 700, "y": 100}
                    },
                    {
                        "id": "pass_output",
                        "type": "output",
                        "data": {"label": "Quality Pass"},
                        "position": {"x": 900, "y": 50}
                    },
                    {
                        "id": "fail_output",
                        "type": "output",
                        "data": {"label": "Quality Fail - Rework Required"},
                        "position": {"x": 900, "y": 150}
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "start", "target": "rekognition"},
                    {"id": "e2", "source": "rekognition", "target": "defect_classifier"},
                    {"id": "e3", "source": "defect_classifier", "target": "quality_decision"},
                    {"id": "e4", "source": "quality_decision", "target": "pass_output", "label": "Pass"},
                    {"id": "e5", "source": "quality_decision", "target": "fail_output", "label": "Fail"}
                ]
            },
            {
                "name": "Predictive Maintenance Analysis",
                "description": "Analyze sensor data to predict equipment maintenance needs",
                "category": "manufacturing",
                "tags": ["predictive-maintenance", "iot", "machine-learning"],
                "nodes": [
                    {
                        "id": "start",
                        "type": "input",
                        "data": {"label": "Sensor Data"},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "data_preprocessing",
                        "type": "custom",
                        "data": {
                            "label": "Data Preprocessing",
                            "config": {
                                "normalize": True,
                                "remove_outliers": True,
                                "feature_engineering": True
                            }
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "anomaly_detection",
                        "type": "sagemaker",
                        "data": {
                            "label": "Anomaly Detection",
                            "config": {
                                "algorithm": "random_cut_forest",
                                "threshold": 0.8
                            }
                        },
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "maintenance_predictor",
                        "type": "sagemaker",
                        "data": {
                            "label": "Maintenance Prediction",
                            "config": {
                                "model_endpoint": "maintenance_prediction_model",
                                "prediction_horizon": "7_days"
                            }
                        },
                        "position": {"x": 700, "y": 100}
                    },
                    {
                        "id": "alert_system",
                        "type": "custom",
                        "data": {
                            "label": "Alert Generation",
                            "config": {
                                "alert_channels": ["email", "sms", "dashboard"],
                                "priority_levels": ["low", "medium", "high", "critical"]
                            }
                        },
                        "position": {"x": 900, "y": 100}
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "start", "target": "data_preprocessing"},
                    {"id": "e2", "source": "data_preprocessing", "target": "anomaly_detection"},
                    {"id": "e3", "source": "anomaly_detection", "target": "maintenance_predictor"},
                    {"id": "e4", "source": "maintenance_predictor", "target": "alert_system"}
                ]
            }
        ]
    
    @staticmethod
    def get_financial_templates() -> List[Dict[str, Any]]:
        """Financial services workflow templates"""
        return [
            {
                "name": "Document Fraud Detection",
                "description": "Automated detection of fraudulent financial documents",
                "category": "financial",
                "tags": ["fraud-detection", "document-analysis", "compliance"],
                "nodes": [
                    {
                        "id": "start",
                        "type": "input",
                        "data": {"label": "Financial Document"},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "textract",
                        "type": "textract",
                        "data": {
                            "label": "Document Analysis",
                            "config": {
                                "features": ["FORMS", "TABLES", "SIGNATURES"],
                                "analyze_id": True
                            }
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "fraud_detection",
                        "type": "sagemaker",
                        "data": {
                            "label": "Fraud Detection Model",
                            "config": {
                                "model_endpoint": "financial_fraud_detector",
                                "confidence_threshold": 0.85
                            }
                        },
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "risk_assessment",
                        "type": "custom",
                        "data": {
                            "label": "Risk Scoring",
                            "config": {
                                "risk_factors": ["document_quality", "data_consistency", "historical_patterns"],
                                "scoring_model": "financial_risk_v2"
                            }
                        },
                        "position": {"x": 700, "y": 100}
                    },
                    {
                        "id": "compliance_check",
                        "type": "custom",
                        "data": {
                            "label": "Regulatory Compliance",
                            "config": {
                                "regulations": ["KYC", "AML", "SOX"],
                                "auto_flag": True
                            }
                        },
                        "position": {"x": 900, "y": 100}
                    },
                    {
                        "id": "output",
                        "type": "output",
                        "data": {"label": "Fraud Assessment Report"},
                        "position": {"x": 1100, "y": 100}
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "start", "target": "textract"},
                    {"id": "e2", "source": "textract", "target": "fraud_detection"},
                    {"id": "e3", "source": "fraud_detection", "target": "risk_assessment"},
                    {"id": "e4", "source": "risk_assessment", "target": "compliance_check"},
                    {"id": "e5", "source": "compliance_check", "target": "output"}
                ]
            },
            {
                "name": "Credit Risk Assessment",
                "description": "Automated credit risk evaluation using multiple data sources",
                "category": "financial",
                "tags": ["credit-risk", "machine-learning", "decision-support"],
                "nodes": [
                    {
                        "id": "start",
                        "type": "input",
                        "data": {"label": "Credit Application"},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "data_collection",
                        "type": "custom",
                        "data": {
                            "label": "Data Aggregation",
                            "config": {
                                "sources": ["credit_bureau", "bank_statements", "employment_verification"],
                                "data_validation": True
                            }
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "credit_scoring",
                        "type": "sagemaker",
                        "data": {
                            "label": "Credit Score Calculation",
                            "config": {
                                "model_endpoint": "credit_scoring_model_v3",
                                "include_alternative_data": True
                            }
                        },
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "risk_categorization",
                        "type": "condition",
                        "data": {
                            "label": "Risk Category",
                            "config": {
                                "categories": {
                                    "low_risk": "score >= 750",
                                    "medium_risk": "650 <= score < 750",
                                    "high_risk": "score < 650"
                                }
                            }
                        },
                        "position": {"x": 700, "y": 100}
                    },
                    {
                        "id": "approval_output",
                        "type": "output",
                        "data": {"label": "Credit Approved"},
                        "position": {"x": 900, "y": 50}
                    },
                    {
                        "id": "review_output",
                        "type": "output",
                        "data": {"label": "Manual Review Required"},
                        "position": {"x": 900, "y": 100}
                    },
                    {
                        "id": "rejection_output",
                        "type": "output",
                        "data": {"label": "Credit Denied"},
                        "position": {"x": 900, "y": 150}
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "start", "target": "data_collection"},
                    {"id": "e2", "source": "data_collection", "target": "credit_scoring"},
                    {"id": "e3", "source": "credit_scoring", "target": "risk_categorization"},
                    {"id": "e4", "source": "risk_categorization", "target": "approval_output", "label": "Low Risk"},
                    {"id": "e5", "source": "risk_categorization", "target": "review_output", "label": "Medium Risk"},
                    {"id": "e6", "source": "risk_categorization", "target": "rejection_output", "label": "High Risk"}
                ]
            }
        ]
    
    @staticmethod
    def get_legal_templates() -> List[Dict[str, Any]]:
        """Legal industry workflow templates"""
        return [
            {
                "name": "Contract Analysis and Review",
                "description": "Automated analysis of legal contracts for key terms and risks",
                "category": "legal",
                "tags": ["contract-analysis", "legal-review", "risk-assessment"],
                "nodes": [
                    {
                        "id": "start",
                        "type": "input",
                        "data": {"label": "Legal Contract"},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "textract",
                        "type": "textract",
                        "data": {
                            "label": "Document Extraction",
                            "config": {
                                "features": ["FORMS", "TABLES"],
                                "preserve_formatting": True
                            }
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "legal_nlp",
                        "type": "comprehend",
                        "data": {
                            "label": "Legal Entity Recognition",
                            "config": {
                                "custom_model": "legal_entities_model",
                                "entity_types": ["PARTY", "DATE", "AMOUNT", "OBLIGATION"]
                            }
                        },
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "clause_extraction",
                        "type": "custom",
                        "data": {
                            "label": "Key Clause Identification",
                            "config": {
                                "clause_types": ["termination", "liability", "indemnification", "governing_law"],
                                "risk_scoring": True
                            }
                        },
                        "position": {"x": 700, "y": 100}
                    },
                    {
                        "id": "compliance_check",
                        "type": "custom",
                        "data": {
                            "label": "Regulatory Compliance",
                            "config": {
                                "jurisdictions": ["federal", "state", "international"],
                                "compliance_frameworks": ["GDPR", "CCPA", "SOX"]
                            }
                        },
                        "position": {"x": 900, "y": 100}
                    },
                    {
                        "id": "output",
                        "type": "output",
                        "data": {"label": "Contract Analysis Report"},
                        "position": {"x": 1100, "y": 100}
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "start", "target": "textract"},
                    {"id": "e2", "source": "textract", "target": "legal_nlp"},
                    {"id": "e3", "source": "legal_nlp", "target": "clause_extraction"},
                    {"id": "e4", "source": "clause_extraction", "target": "compliance_check"},
                    {"id": "e5", "source": "compliance_check", "target": "output"}
                ]
            }
        ]
    
    @staticmethod
    def get_retail_templates() -> List[Dict[str, Any]]:
        """Retail industry workflow templates"""
        return [
            {
                "name": "Customer Sentiment Analysis",
                "description": "Analyze customer reviews and feedback for insights",
                "category": "retail",
                "tags": ["customer-sentiment", "review-analysis", "business-intelligence"],
                "nodes": [
                    {
                        "id": "start",
                        "type": "input",
                        "data": {"label": "Customer Reviews"},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "sentiment",
                        "type": "comprehend",
                        "data": {
                            "label": "Sentiment Analysis",
                            "config": {"analysis_type": "sentiment"}
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "topics",
                        "type": "comprehend",
                        "data": {
                            "label": "Topic Modeling",
                            "config": {"analysis_type": "topics"}
                        },
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "product_categorization",
                        "type": "custom",
                        "data": {
                            "label": "Product Category Analysis",
                            "config": {
                                "categories": ["quality", "price", "service", "delivery"],
                                "sentiment_mapping": True
                            }
                        },
                        "position": {"x": 700, "y": 100}
                    },
                    {
                        "id": "output",
                        "type": "output",
                        "data": {"label": "Customer Insights Dashboard"},
                        "position": {"x": 900, "y": 100}
                    }
                ],
                "edges": [
                    {"id": "e1", "source": "start", "target": "sentiment"},
                    {"id": "e2", "source": "start", "target": "topics"},
                    {"id": "e3", "source": "sentiment", "target": "product_categorization"},
                    {"id": "e4", "source": "topics", "target": "product_categorization"},
                    {"id": "e5", "source": "product_categorization", "target": "output"}
                ]
            }
        ]
    
    @staticmethod
    def get_all_templates() -> Dict[str, List[Dict[str, Any]]]:
        """Get all workflow templates organized by industry"""
        return {
            "healthcare": WorkflowTemplateManager.get_healthcare_templates(),
            "manufacturing": WorkflowTemplateManager.get_manufacturing_templates(),
            "financial": WorkflowTemplateManager.get_financial_templates(),
            "legal": WorkflowTemplateManager.get_legal_templates(),
            "retail": WorkflowTemplateManager.get_retail_templates()
        }
    
    @staticmethod
    def get_template_by_id(template_id: str) -> Dict[str, Any]:
        """Get a specific template by ID"""
        all_templates = WorkflowTemplateManager.get_all_templates()
        for industry, templates in all_templates.items():
            for template in templates:
                if template.get("id") == template_id:
                    return template
        return None
    
    @staticmethod
    def search_templates(query: str, industry: str = None) -> List[Dict[str, Any]]:
        """Search templates by query and optionally filter by industry"""
        all_templates = WorkflowTemplateManager.get_all_templates()
        results = []
        
        for industry_name, templates in all_templates.items():
            if industry and industry_name != industry:
                continue
                
            for template in templates:
                # Search in name, description, and tags
                search_text = f"{template['name']} {template['description']} {' '.join(template['tags'])}".lower()
                if query.lower() in search_text:
                    template_copy = template.copy()
                    template_copy["industry"] = industry_name
                    results.append(template_copy)
        
        return results
