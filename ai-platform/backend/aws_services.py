import boto3
import json
import os
from typing import Dict, Any, List
from botocore.exceptions import ClientError

class AWSServices:
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.textract_client = boto3.client('textract', region_name=self.region)
        self.comprehend_client = boto3.client('comprehend', region_name=self.region)
        self.rekognition_client = boto3.client('rekognition', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        
        # S3 bucket names from environment
        self.data_bucket = os.getenv('S3_DATA_BUCKET')
        self.models_bucket = os.getenv('S3_MODELS_BUCKET')
        self.static_bucket = os.getenv('S3_STATIC_BUCKET')
    
    async def health_check(self) -> str:
        """Check AWS services health"""
        try:
            # Test S3 access
            self.s3_client.head_bucket(Bucket=self.data_bucket)
            return "healthy"
        except Exception as e:
            return f"unhealthy: {str(e)}"
    
    async def upload_file(self, file_content: bytes, file_name: str, bucket_type: str = 'data') -> str:
        """Upload file to S3"""
        bucket_map = {
            'data': self.data_bucket,
            'models': self.models_bucket,
            'static': self.static_bucket
        }
        
        bucket = bucket_map.get(bucket_type, self.data_bucket)
        
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=file_name,
                Body=file_content
            )
            return f"s3://{bucket}/{file_name}"
        except ClientError as e:
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def analyze_document(self, s3_uri: str) -> Dict[str, Any]:
        """Analyze document using AWS Textract"""
        try:
            # Parse S3 URI
            bucket, key = s3_uri.replace('s3://', '').split('/', 1)
            
            response = self.textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                FeatureTypes=['TABLES', 'FORMS']
            )
            
            # Extract text and structured data
            extracted_text = []
            tables = []
            forms = []
            
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    extracted_text.append(block['Text'])
                elif block['BlockType'] == 'TABLE':
                    # Process table data
                    tables.append(self._process_table(block, response['Blocks']))
                elif block['BlockType'] == 'KEY_VALUE_SET':
                    # Process form data
                    forms.append(self._process_form(block, response['Blocks']))
            
            return {
                'text': '\n'.join(extracted_text),
                'tables': tables,
                'forms': forms,
                'confidence': self._calculate_average_confidence(response['Blocks'])
            }
        
        except ClientError as e:
            raise Exception(f"Document analysis failed: {str(e)}")
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze text sentiment using AWS Comprehend"""
        try:
            response = self.comprehend_client.detect_sentiment(
                Text=text,
                LanguageCode='en'
            )
            
            return {
                'sentiment': response['Sentiment'],
                'confidence_scores': response['SentimentScore']
            }
        
        except ClientError as e:
            raise Exception(f"Sentiment analysis failed: {str(e)}")
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text using AWS Comprehend"""
        try:
            response = self.comprehend_client.detect_entities(
                Text=text,
                LanguageCode='en'
            )
            
            return [
                {
                    'text': entity['Text'],
                    'type': entity['Type'],
                    'confidence': entity['Score']
                }
                for entity in response['Entities']
            ]
        
        except ClientError as e:
            raise Exception(f"Entity extraction failed: {str(e)}")
    
    async def analyze_image(self, s3_uri: str) -> Dict[str, Any]:
        """Analyze image using AWS Rekognition"""
        try:
            # Parse S3 URI
            bucket, key = s3_uri.replace('s3://', '').split('/', 1)
            
            # Detect labels
            labels_response = self.rekognition_client.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                MaxLabels=20,
                MinConfidence=70
            )
            
            # Detect text in image
            text_response = self.rekognition_client.detect_text(
                Image={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
            
            return {
                'labels': [
                    {
                        'name': label['Name'],
                        'confidence': label['Confidence']
                    }
                    for label in labels_response['Labels']
                ],
                'text': [
                    {
                        'text': text['DetectedText'],
                        'confidence': text['Confidence'],
                        'type': text['Type']
                    }
                    for text in text_response['TextDetections']
                ]
            }
        
        except ClientError as e:
            raise Exception(f"Image analysis failed: {str(e)}")
    
    async def execute_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow based on configuration"""
        try:
            results = {}
            
            for step in workflow_config.get('steps', []):
                step_type = step.get('type')
                step_config = step.get('config', {})
                
                if step_type == 'document_analysis':
                    s3_uri = step_config.get('input_uri')
                    results[step['id']] = await self.analyze_document(s3_uri)
                
                elif step_type == 'sentiment_analysis':
                    text = step_config.get('text') or results.get(step_config.get('input_step'), {}).get('text', '')
                    results[step['id']] = await self.analyze_sentiment(text)
                
                elif step_type == 'entity_extraction':
                    text = step_config.get('text') or results.get(step_config.get('input_step'), {}).get('text', '')
                    results[step['id']] = await self.extract_entities(text)
                
                elif step_type == 'image_analysis':
                    s3_uri = step_config.get('input_uri')
                    results[step['id']] = await self.analyze_image(s3_uri)
            
            return {
                'status': 'completed',
                'results': results,
                'workflow_id': workflow_config.get('id')
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'workflow_id': workflow_config.get('id')
            }
    
    def _process_table(self, table_block: Dict, all_blocks: List[Dict]) -> Dict[str, Any]:
        """Process table data from Textract response"""
        # Simplified table processing - in production, this would be more sophisticated
        return {
            'id': table_block['Id'],
            'confidence': table_block.get('Confidence', 0),
            'rows': []  # Would extract actual table data here
        }
    
    def _process_form(self, form_block: Dict, all_blocks: List[Dict]) -> Dict[str, Any]:
        """Process form data from Textract response"""
        # Simplified form processing - in production, this would be more sophisticated
        return {
            'id': form_block['Id'],
            'confidence': form_block.get('Confidence', 0),
            'key_value_pairs': []  # Would extract actual form data here
        }
    
    def _calculate_average_confidence(self, blocks: List[Dict]) -> float:
        """Calculate average confidence score from Textract blocks"""
        confidences = [block.get('Confidence', 0) for block in blocks if 'Confidence' in block]
        return sum(confidences) / len(confidences) if confidences else 0
