import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import boto3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os

from models import User, Project, Analytics, Notification
from database import get_db

class MarketingAutomationEngine:
    """Comprehensive marketing automation system"""
    
    def __init__(self):
        self.ses_client = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.sns_client = boto3.client('sns', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        
    async def run_automation_campaigns(self, db: Session):
        """Run all active marketing automation campaigns"""
        try:
            # Welcome sequence for new users
            await self.run_welcome_sequence(db)
            
            # Onboarding follow-up
            await self.run_onboarding_followup(db)
            
            # Re-engagement campaigns
            await self.run_reengagement_campaigns(db)
            
            # Feature announcement campaigns
            await self.run_feature_announcements(db)
            
            # Success milestone celebrations
            await self.run_milestone_campaigns(db)
            
            # Feedback collection campaigns
            await self.run_feedback_campaigns(db)
            
        except Exception as e:
            print(f"Error running automation campaigns: {str(e)}")

    async def run_welcome_sequence(self, db: Session):
        """Welcome email sequence for new users"""
        # Find users registered in the last 24 hours who haven't received welcome emails
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        new_users = db.query(User).filter(
            and_(
                User.created_at >= yesterday,
                User.is_active == True
            )
        ).all()
        
        for user in new_users:
            # Check if welcome email already sent
            if not self._has_received_campaign(db, user.id, 'welcome_sequence'):
                await self._send_welcome_email(user)
                self._mark_campaign_sent(db, user.id, 'welcome_sequence', 'welcome_day_0')

    async def run_onboarding_followup(self, db: Session):
        """Follow-up emails for onboarding completion"""
        # Users registered 3 days ago who haven't created a project
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        
        inactive_users = db.query(User).filter(
            and_(
                User.created_at <= three_days_ago,
                User.created_at >= three_days_ago - timedelta(hours=24),
                User.is_active == True
            )
        ).all()
        
        for user in inactive_users:
            # Check if user has created any projects
            project_count = db.query(Project).filter(Project.owner_id == user.id).count()
            
            if project_count == 0 and not self._has_received_campaign(db, user.id, 'onboarding_followup'):
                await self._send_onboarding_followup_email(user)
                self._mark_campaign_sent(db, user.id, 'onboarding_followup', 'day_3_no_project')

    async def run_reengagement_campaigns(self, db: Session):
        """Re-engage inactive users"""
        # Users who haven't logged in for 14 days
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        
        # Find users with no recent activity
        inactive_users = db.query(User).filter(
            and_(
                User.updated_at <= two_weeks_ago,
                User.is_active == True
            )
        ).all()
        
        for user in inactive_users:
            if not self._has_received_campaign(db, user.id, 'reengagement_14d'):
                await self._send_reengagement_email(user)
                self._mark_campaign_sent(db, user.id, 'reengagement_14d', 'inactive_14_days')

    async def run_feature_announcements(self, db: Session):
        """Announce new features to users"""
        # Get all active users
        active_users = db.query(User).filter(User.is_active == True).all()
        
        # Example: New AI model marketplace announcement
        feature_announcement = {
            'feature_name': 'AI Model Marketplace',
            'announcement_date': datetime.utcnow().date(),
            'campaign_id': 'marketplace_launch_2025'
        }
        
        for user in active_users:
            if not self._has_received_campaign(db, user.id, feature_announcement['campaign_id']):
                await self._send_feature_announcement_email(user, feature_announcement)
                self._mark_campaign_sent(db, user.id, feature_announcement['campaign_id'], 'feature_announcement')

    async def run_milestone_campaigns(self, db: Session):
        """Celebrate user milestones"""
        # Find users who completed their first project
        users_with_projects = db.query(User).join(Project).filter(
            and_(
                Project.status == 'completed',
                User.is_active == True
            )
        ).all()
        
        for user in users_with_projects:
            project_count = db.query(Project).filter(
                and_(
                    Project.owner_id == user.id,
                    Project.status == 'completed'
                )
            ).count()
            
            # First project completion
            if project_count == 1 and not self._has_received_campaign(db, user.id, 'first_project_complete'):
                await self._send_milestone_email(user, 'first_project')
                self._mark_campaign_sent(db, user.id, 'first_project_complete', 'milestone_achievement')
            
            # Fifth project completion
            elif project_count == 5 and not self._has_received_campaign(db, user.id, 'fifth_project_complete'):
                await self._send_milestone_email(user, 'fifth_project')
                self._mark_campaign_sent(db, user.id, 'fifth_project_complete', 'milestone_achievement')

    async def run_feedback_campaigns(self, db: Session):
        """Collect user feedback"""
        # Users who have been active for 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        established_users = db.query(User).filter(
            and_(
                User.created_at <= thirty_days_ago,
                User.is_active == True
            )
        ).all()
        
        for user in established_users:
            if not self._has_received_campaign(db, user.id, 'feedback_request_30d'):
                await self._send_feedback_request_email(user)
                self._mark_campaign_sent(db, user.id, 'feedback_request_30d', 'feedback_collection')

    async def _send_welcome_email(self, user: User):
        """Send welcome email to new user"""
        subject = f"Welcome to AI Platform, {user.full_name}!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">Welcome to AI Platform!</h1>
                
                <p>Hi {user.full_name},</p>
                
                <p>Welcome to AI Platform! We're excited to have you join our community of innovators who are transforming their businesses with AI.</p>
                
                <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1e40af; margin-top: 0;">Get Started in 3 Easy Steps:</h3>
                    <ol>
                        <li><strong>Create Your First Project</strong> - Define your AI automation goals</li>
                        <li><strong>Build a Workflow</strong> - Use our drag-and-drop workflow builder</li>
                        <li><strong>Deploy and Monitor</strong> - Watch your AI solution work</li>
                    </ol>
                </div>
                
                <p>Need help getting started? Our team is here to support you:</p>
                <ul>
                    <li>📚 <a href="https://docs.aiplatform.com">Documentation & Tutorials</a></li>
                    <li>💬 <a href="https://support.aiplatform.com">24/7 Support Chat</a></li>
                    <li>🎥 <a href="https://aiplatform.com/webinars">Weekly Demo Webinars</a></li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.aiplatform.com/dashboard" 
                       style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Start Building Now
                    </a>
                </div>
                
                <p>Best regards,<br>The AI Platform Team</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 12px; color: #6b7280;">
                    You're receiving this email because you signed up for AI Platform. 
                    <a href="https://aiplatform.com/unsubscribe">Unsubscribe</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        await self._send_email(user.email, subject, html_content)

    async def _send_onboarding_followup_email(self, user: User):
        """Send onboarding follow-up email"""
        subject = "Need help getting started with AI Platform?"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">Let's Get Your First AI Project Started!</h1>
                
                <p>Hi {user.full_name},</p>
                
                <p>We noticed you haven't created your first project yet. No worries - we're here to help you get started!</p>
                
                <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                    <h3 style="color: #92400e; margin-top: 0;">🚀 Quick Start Options:</h3>
                    <ul>
                        <li><strong>Use a Template</strong> - Start with industry-specific workflows</li>
                        <li><strong>Schedule a Demo</strong> - Get personalized guidance from our experts</li>
                        <li><strong>Join Our Webinar</strong> - Learn from other successful implementations</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.aiplatform.com/templates" 
                       style="background-color: #f59e0b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-right: 10px;">
                        Browse Templates
                    </a>
                    <a href="https://calendly.com/aiplatform/demo" 
                       style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Schedule Demo
                    </a>
                </div>
                
                <p>Questions? Reply to this email or chat with our support team anytime.</p>
                
                <p>Best regards,<br>The AI Platform Team</p>
            </div>
        </body>
        </html>
        """
        
        await self._send_email(user.email, subject, html_content)

    async def _send_reengagement_email(self, user: User):
        """Send re-engagement email to inactive users"""
        subject = "We miss you! Here's what's new at AI Platform"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">We Miss You, {user.full_name}!</h1>
                
                <p>It's been a while since we've seen you on AI Platform. We've been busy adding exciting new features that we think you'll love!</p>
                
                <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #065f46; margin-top: 0;">🆕 What's New:</h3>
                    <ul>
                        <li><strong>AI Model Marketplace</strong> - Access 100+ pre-trained models</li>
                        <li><strong>Real-time Collaboration</strong> - Work with your team in real-time</li>
                        <li><strong>Advanced Analytics</strong> - Deep insights into your AI performance</li>
                        <li><strong>Industry Templates</strong> - Ready-to-use workflows for your industry</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.aiplatform.com/dashboard" 
                       style="background-color: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Explore New Features
                    </a>
                </div>
                
                <p>Ready to dive back in? We're here to help you succeed!</p>
                
                <p>Best regards,<br>The AI Platform Team</p>
            </div>
        </body>
        </html>
        """
        
        await self._send_email(user.email, subject, html_content)

    async def _send_feature_announcement_email(self, user: User, feature: Dict[str, Any]):
        """Send feature announcement email"""
        subject = f"🎉 Introducing {feature['feature_name']} - Now Available!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">🎉 {feature['feature_name']} is Here!</h1>
                
                <p>Hi {user.full_name},</p>
                
                <p>We're excited to announce the launch of our new {feature['feature_name']}! This powerful addition to AI Platform will help you achieve even more with your AI automation projects.</p>
                
                <div style="background-color: #ede9fe; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #5b21b6; margin-top: 0;">✨ Key Benefits:</h3>
                    <ul>
                        <li>Access to 100+ pre-trained AI models</li>
                        <li>Easy integration with your existing workflows</li>
                        <li>Pay-per-use pricing model</li>
                        <li>Community ratings and reviews</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.aiplatform.com/marketplace" 
                       style="background-color: #7c3aed; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Explore Marketplace
                    </a>
                </div>
                
                <p>Questions about the new feature? Our support team is ready to help!</p>
                
                <p>Best regards,<br>The AI Platform Team</p>
            </div>
        </body>
        </html>
        """
        
        await self._send_email(user.email, subject, html_content)

    async def _send_milestone_email(self, user: User, milestone_type: str):
        """Send milestone celebration email"""
        if milestone_type == 'first_project':
            subject = "🎉 Congratulations on completing your first AI project!"
            milestone_text = "your first AI automation project"
            next_steps = "Ready to tackle your next challenge? Explore our advanced workflow templates or connect with our consultant network."
        elif milestone_type == 'fifth_project':
            subject = "🏆 Amazing! You've completed 5 AI projects!"
            milestone_text = "five successful AI automation projects"
            next_steps = "You're becoming an AI automation expert! Consider sharing your success story with our community or exploring our enterprise features."
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">🎉 Congratulations, {user.full_name}!</h1>
                
                <p>We're thrilled to celebrate this milestone with you - you've successfully completed {milestone_text}!</p>
                
                <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                    <h2 style="color: #92400e; margin: 0; font-size: 2em;">🏆</h2>
                    <h3 style="color: #92400e; margin: 10px 0;">Milestone Achieved!</h3>
                </div>
                
                <p>{next_steps}</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.aiplatform.com/dashboard" 
                       style="background-color: #f59e0b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Continue Your Journey
                    </a>
                </div>
                
                <p>Keep up the amazing work!</p>
                
                <p>Best regards,<br>The AI Platform Team</p>
            </div>
        </body>
        </html>
        """
        
        await self._send_email(user.email, subject, html_content)

    async def _send_feedback_request_email(self, user: User):
        """Send feedback request email"""
        subject = "Help us improve AI Platform - 2 minute survey"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">Your Opinion Matters!</h1>
                
                <p>Hi {user.full_name},</p>
                
                <p>You've been using AI Platform for a month now, and we'd love to hear about your experience!</p>
                
                <p>Your feedback helps us build better features and improve the platform for everyone. This quick survey takes just 2 minutes.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://survey.aiplatform.com/feedback" 
                       style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Share Your Feedback
                    </a>
                </div>
                
                <p>As a thank you, we'll send you a $25 credit for your AI Platform account once you complete the survey!</p>
                
                <p>Thank you for helping us improve!</p>
                
                <p>Best regards,<br>The AI Platform Team</p>
            </div>
        </body>
        </html>
        """
        
        await self._send_email(user.email, subject, html_content)

    async def _send_email(self, to_email: str, subject: str, html_content: str):
        """Send email using AWS SES"""
        try:
            response = self.ses_client.send_email(
                Source='noreply@aiplatform.com',
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Html': {'Data': html_content, 'Charset': 'UTF-8'}
                    }
                }
            )
            print(f"Email sent successfully to {to_email}: {response['MessageId']}")
        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")

    def _has_received_campaign(self, db: Session, user_id: int, campaign_id: str) -> bool:
        """Check if user has already received a specific campaign"""
        # This would typically check a marketing_campaigns table
        # For now, we'll use the analytics table as a simple implementation
        campaign_record = db.query(Analytics).filter(
            and_(
                Analytics.user_id == user_id,
                Analytics.event_type == 'email_campaign',
                Analytics.event_data.contains(campaign_id)
            )
        ).first()
        
        return campaign_record is not None

    def _mark_campaign_sent(self, db: Session, user_id: int, campaign_id: str, campaign_type: str):
        """Mark that a campaign has been sent to a user"""
        analytics_record = Analytics(
            user_id=user_id,
            event_type='email_campaign',
            event_data={
                'campaign_id': campaign_id,
                'campaign_type': campaign_type,
                'sent_at': datetime.utcnow().isoformat()
            }
        )
        
        db.add(analytics_record)
        db.commit()

# Lead Scoring System
class LeadScoringEngine:
    """Automated lead scoring based on user behavior"""
    
    @staticmethod
    def calculate_lead_score(db: Session, user_id: int) -> int:
        """Calculate lead score for a user"""
        score = 0
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        
        # Base score for registration
        score += 10
        
        # Company information provided
        if user.company:
            score += 15
        
        # Project creation activity
        project_count = db.query(Project).filter(Project.owner_id == user_id).count()
        score += min(project_count * 20, 100)  # Max 100 points for projects
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_activity = db.query(Analytics).filter(
            and_(
                Analytics.user_id == user_id,
                Analytics.timestamp >= week_ago
            )
        ).count()
        score += min(recent_activity * 2, 50)  # Max 50 points for recent activity
        
        # Workflow executions
        workflow_executions = db.query(Analytics).filter(
            and_(
                Analytics.user_id == user_id,
                Analytics.event_type == 'workflow_execution'
            )
        ).count()
        score += min(workflow_executions * 10, 100)  # Max 100 points for executions
        
        return min(score, 1000)  # Cap at 1000 points

    @staticmethod
    def get_lead_category(score: int) -> str:
        """Categorize lead based on score"""
        if score >= 200:
            return 'hot'
        elif score >= 100:
            return 'warm'
        elif score >= 50:
            return 'cold'
        else:
            return 'new'

# Social Media Automation
class SocialMediaAutomation:
    """Automated social media posting and engagement"""
    
    def __init__(self):
        # Initialize social media API clients
        pass
    
    async def schedule_content(self, content: Dict[str, Any]):
        """Schedule social media content"""
        # Implementation for scheduling posts across platforms
        pass
    
    async def monitor_mentions(self):
        """Monitor brand mentions across social platforms"""
        # Implementation for social listening
        pass
