'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Bot, Zap, Shield, BarChart3 } from 'lucide-react'

export default function HomePage() {
  const [email, setEmail] = useState('')

  const handleGetStarted = (e: React.FormEvent) => {
    e.preventDefault()
    // Handle email signup
    console.log('Email signup:', email)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Bot className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">AI Platform</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/login" className="text-gray-700 hover:text-blue-600">
                Sign In
              </Link>
              <Link 
                href="/register" 
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Transform Your Business with
            <span className="text-blue-600"> AI Solutions</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Professional AI consulting and automation platform designed for SMBs and enterprises. 
            Get expert guidance, powerful tools, and measurable results.
          </p>
          
          <form onSubmit={handleGetStarted} className="max-w-md mx-auto mb-8">
            <div className="flex gap-2">
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
              <button
                type="submit"
                className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 flex items-center gap-2"
              >
                Start Free <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </form>

          <p className="text-sm text-gray-500">
            Free 14-day trial • No credit card required • Cancel anytime
          </p>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Everything you need to succeed with AI
            </h2>
            <p className="text-lg text-gray-600">
              From strategy to implementation, we provide the complete AI transformation solution
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bot className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">AI Consulting</h3>
              <p className="text-gray-600">
                Expert guidance from AI specialists to develop your transformation strategy
              </p>
            </div>

            <div className="text-center">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Zap className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Automation Platform</h3>
              <p className="text-gray-600">
                No-code platform to build and deploy AI workflows for your business
              </p>
            </div>

            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Enterprise Security</h3>
              <p className="text-gray-600">
                Bank-level security with compliance for GDPR, HIPAA, and SOX
              </p>
            </div>

            <div className="text-center">
              <div className="bg-orange-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="h-8 w-8 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">ROI Analytics</h3>
              <p className="text-gray-600">
                Track and measure the business impact of your AI implementations
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to transform your business with AI?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join hundreds of businesses already using our platform to drive growth and efficiency
          </p>
          <Link 
            href="/register"
            className="bg-white text-blue-600 px-8 py-3 rounded-md font-semibold hover:bg-gray-100 inline-flex items-center gap-2"
          >
            Get Started Today <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center mb-4">
                <Bot className="h-8 w-8 text-blue-400" />
                <span className="ml-2 text-xl font-bold">AI Platform</span>
              </div>
              <p className="text-gray-400">
                Professional AI consulting and automation for modern businesses.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Services</h3>
              <ul className="space-y-2 text-gray-400">
                <li>AI Consulting</li>
                <li>Platform Solutions</li>
                <li>Custom Development</li>
                <li>Training & Support</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Industries</h3>
              <ul className="space-y-2 text-gray-400">
                <li>Professional Services</li>
                <li>Healthcare</li>
                <li>Manufacturing</li>
                <li>Financial Services</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-gray-400">
                <li>About Us</li>
                <li>Contact</li>
                <li>Privacy Policy</li>
                <li>Terms of Service</li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2025 AI Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
