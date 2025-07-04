'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Star, Search, Filter, Tag, TrendingUp, Clock, DollarSign } from 'lucide-react';

interface AIModel {
  id: number;
  name: string;
  description: string;
  model_type: string;
  provider: string;
  version: string;
  pricing_model: string;
  price_per_unit: number;
  category: string;
  tags: string[];
  is_featured: boolean;
  total_requests: number;
  average_response_time: number;
  success_rate: number;
  average_rating: number;
  review_count: number;
  creator_name: string;
  created_at: string;
}

export default function MarketplacePage() {
  const [models, setModels] = useState<AIModel[]>([]);
  const [filteredModels, setFilteredModels] = useState<AIModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedProvider, setSelectedProvider] = useState('all');
  const [sortBy, setSortBy] = useState('featured');
  const router = useRouter();

  const categories = [
    'all', 'nlp', 'computer_vision', 'audio', 'data_analysis', 'automation'
  ];

  const providers = [
    'all', 'openai', 'huggingface', 'aws', 'google', 'custom'
  ];

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    fetchModels(token);
  }, [router]);

  useEffect(() => {
    filterAndSortModels();
  }, [models, searchTerm, selectedCategory, selectedProvider, sortBy]);

  const fetchModels = async (token: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/marketplace/models`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setModels(data);
      } else {
        setError('Failed to load AI models');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortModels = () => {
    let filtered = models.filter(model => {
      const matchesSearch = model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           model.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           model.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      
      const matchesCategory = selectedCategory === 'all' || model.category === selectedCategory;
      const matchesProvider = selectedProvider === 'all' || model.provider === selectedProvider;
      
      return matchesSearch && matchesCategory && matchesProvider;
    });

    // Sort models
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'featured':
          if (a.is_featured && !b.is_featured) return -1;
          if (!a.is_featured && b.is_featured) return 1;
          return b.average_rating - a.average_rating;
        case 'rating':
          return b.average_rating - a.average_rating;
        case 'popular':
          return b.total_requests - a.total_requests;
        case 'newest':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'price_low':
          return a.price_per_unit - b.price_per_unit;
        case 'price_high':
          return b.price_per_unit - a.price_per_unit;
        default:
          return 0;
      }
    });

    setFilteredModels(filtered);
  };

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < Math.floor(rating) ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
      />
    ));
  };

  const formatPrice = (price: number, pricingModel: string) => {
    if (pricingModel === 'free') return 'Free';
    if (pricingModel === 'per_request') return `$${price.toFixed(4)}/request`;
    if (pricingModel === 'per_token') return `$${price.toFixed(6)}/token`;
    if (pricingModel === 'subscription') return `$${price}/month`;
    return `$${price}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/dashboard" className="text-xl font-semibold text-gray-900">
                AI Platform
              </Link>
              <span className="mx-2 text-gray-400">/</span>
              <span className="text-gray-900">AI Model Marketplace</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/marketplace/submit"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Submit Model
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">AI Model Marketplace</h1>
          <p className="mt-2 text-gray-600">
            Discover and integrate cutting-edge AI models into your workflows
          </p>
        </div>

        {/* Search and Filters */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search models..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category === 'all' ? 'All Categories' : category.replace('_', ' ').toUpperCase()}
                </option>
              ))}
            </select>

            {/* Provider Filter */}
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {providers.map(provider => (
                <option key={provider} value={provider}>
                  {provider === 'all' ? 'All Providers' : provider.toUpperCase()}
                </option>
              ))}
            </select>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="featured">Featured</option>
              <option value="rating">Highest Rated</option>
              <option value="popular">Most Popular</option>
              <option value="newest">Newest</option>
              <option value="price_low">Price: Low to High</option>
              <option value="price_high">Price: High to Low</option>
            </select>
          </div>
        </div>

        {/* Models Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredModels.map((model) => (
            <div key={model.id} className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
              <div className="p-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="text-lg font-semibold text-gray-900">{model.name}</h3>
                      {model.is_featured && (
                        <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full">
                          Featured
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">by {model.creator_name}</p>
                  </div>
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                    {model.provider.toUpperCase()}
                  </span>
                </div>

                {/* Description */}
                <p className="text-gray-600 text-sm mb-4 line-clamp-3">{model.description}</p>

                {/* Tags */}
                <div className="flex flex-wrap gap-1 mb-4">
                  {model.tags.slice(0, 3).map((tag, index) => (
                    <span key={index} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
                      {tag}
                    </span>
                  ))}
                  {model.tags.length > 3 && (
                    <span className="text-gray-500 text-xs">+{model.tags.length - 3} more</span>
                  )}
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                  <div className="flex items-center space-x-1">
                    <div className="flex">{renderStars(model.average_rating)}</div>
                    <span className="text-gray-600">({model.review_count})</span>
                  </div>
                  <div className="flex items-center space-x-1 text-gray-600">
                    <TrendingUp className="w-4 h-4" />
                    <span>{model.total_requests.toLocaleString()} uses</span>
                  </div>
                  <div className="flex items-center space-x-1 text-gray-600">
                    <Clock className="w-4 h-4" />
                    <span>{model.average_response_time}ms avg</span>
                  </div>
                  <div className="flex items-center space-x-1 text-gray-600">
                    <span className="text-green-600">✓</span>
                    <span>{model.success_rate}% success</span>
                  </div>
                </div>

                {/* Price */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1">
                    <DollarSign className="w-4 h-4 text-gray-600" />
                    <span className="font-semibold text-gray-900">
                      {formatPrice(model.price_per_unit, model.pricing_model)}
                    </span>
                  </div>
                  <Link
                    href={`/marketplace/models/${model.id}`}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                  >
                    View Details
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredModels.length === 0 && !loading && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg">No models found matching your criteria</div>
            <p className="text-gray-400 mt-2">Try adjusting your search or filters</p>
          </div>
        )}
      </div>
    </div>
  );
}
