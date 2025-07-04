'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  Star, MapPin, Clock, DollarSign, Filter, Search, 
  Award, Briefcase, Users, MessageCircle, Calendar
} from 'lucide-react';

interface Consultant {
  id: number;
  full_name: string;
  bio: string;
  skills: string[];
  hourly_rate: number;
  availability: string;
  rating: number;
  review_count: number;
  projects_completed: number;
  specializations: string[];
  location: string;
  experience_years: number;
  certifications: string[];
  languages: string[];
  response_time: string;
  success_rate: number;
  profile_image?: string;
}

export default function ConsultantsPage() {
  const [consultants, setConsultants] = useState<Consultant[]>([]);
  const [filteredConsultants, setFilteredConsultants] = useState<Consultant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSkill, setSelectedSkill] = useState('all');
  const [priceRange, setPriceRange] = useState('all');
  const [availabilityFilter, setAvailabilityFilter] = useState('all');
  const [sortBy, setSortBy] = useState('rating');
  const router = useRouter();

  const skillOptions = [
    'all', 'machine-learning', 'nlp', 'computer-vision', 'data-science',
    'automation', 'cloud-architecture', 'ai-strategy', 'process-optimization'
  ];

  const priceRanges = [
    { value: 'all', label: 'All Rates' },
    { value: '0-50', label: '$0 - $50/hr' },
    { value: '50-100', label: '$50 - $100/hr' },
    { value: '100-200', label: '$100 - $200/hr' },
    { value: '200+', label: '$200+/hr' }
  ];

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    fetchConsultants(token);
  }, [router]);

  useEffect(() => {
    filterAndSortConsultants();
  }, [consultants, searchTerm, selectedSkill, priceRange, availabilityFilter, sortBy]);

  const fetchConsultants = async (token: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/consultants`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConsultants(data);
      } else {
        setError('Failed to load consultants');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortConsultants = () => {
    let filtered = consultants.filter(consultant => {
      const matchesSearch = consultant.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           consultant.bio.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           consultant.skills.some(skill => skill.toLowerCase().includes(searchTerm.toLowerCase()));
      
      const matchesSkill = selectedSkill === 'all' || 
                          consultant.skills.some(skill => skill.toLowerCase().includes(selectedSkill));
      
      const matchesPrice = priceRange === 'all' || (() => {
        const rate = consultant.hourly_rate;
        switch (priceRange) {
          case '0-50': return rate <= 50;
          case '50-100': return rate > 50 && rate <= 100;
          case '100-200': return rate > 100 && rate <= 200;
          case '200+': return rate > 200;
          default: return true;
        }
      })();
      
      const matchesAvailability = availabilityFilter === 'all' || 
                                 consultant.availability === availabilityFilter;
      
      return matchesSearch && matchesSkill && matchesPrice && matchesAvailability;
    });

    // Sort consultants
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'rating':
          return b.rating - a.rating;
        case 'price_low':
          return a.hourly_rate - b.hourly_rate;
        case 'price_high':
          return b.hourly_rate - a.hourly_rate;
        case 'experience':
          return b.experience_years - a.experience_years;
        case 'projects':
          return b.projects_completed - a.projects_completed;
        default:
          return 0;
      }
    });

    setFilteredConsultants(filtered);
  };

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < Math.floor(rating) ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
      />
    ));
  };

  const handleHireConsultant = (consultantId: number) => {
    router.push(`/consultants/${consultantId}/hire`);
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
              <span className="text-gray-900">Find Consultants</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/consultants/apply"
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Become a Consultant
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
          <h1 className="text-3xl font-bold text-gray-900">Find AI Consultants</h1>
          <p className="mt-2 text-gray-600">
            Connect with expert AI consultants to accelerate your projects
          </p>
        </div>

        {/* Search and Filters */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search consultants..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Skill Filter */}
            <select
              value={selectedSkill}
              onChange={(e) => setSelectedSkill(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {skillOptions.map(skill => (
                <option key={skill} value={skill}>
                  {skill === 'all' ? 'All Skills' : skill.replace('-', ' ').toUpperCase()}
                </option>
              ))}
            </select>

            {/* Price Range */}
            <select
              value={priceRange}
              onChange={(e) => setPriceRange(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {priceRanges.map(range => (
                <option key={range.value} value={range.value}>
                  {range.label}
                </option>
              ))}
            </select>

            {/* Availability */}
            <select
              value={availabilityFilter}
              onChange={(e) => setAvailabilityFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Availability</option>
              <option value="available">Available Now</option>
              <option value="busy">Busy</option>
              <option value="part-time">Part-time Only</option>
            </select>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="rating">Highest Rated</option>
              <option value="price_low">Price: Low to High</option>
              <option value="price_high">Price: High to Low</option>
              <option value="experience">Most Experienced</option>
              <option value="projects">Most Projects</option>
            </select>
          </div>
        </div>

        {/* Consultants Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredConsultants.map((consultant) => (
            <div key={consultant.id} className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
              <div className="p-6">
                {/* Header */}
                <div className="flex items-start space-x-4 mb-4">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                    {consultant.profile_image ? (
                      <img
                        src={consultant.profile_image}
                        alt={consultant.full_name}
                        className="w-16 h-16 rounded-full object-cover"
                      />
                    ) : (
                      <span className="text-blue-600 font-semibold text-lg">
                        {consultant.full_name.split(' ').map(n => n[0]).join('')}
                      </span>
                    )}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">{consultant.full_name}</h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <div className="flex">{renderStars(consultant.rating)}</div>
                      <span className="text-sm text-gray-600">({consultant.review_count})</span>
                    </div>
                    <div className="flex items-center space-x-1 mt-1 text-sm text-gray-600">
                      <MapPin className="w-4 h-4" />
                      <span>{consultant.location}</span>
                    </div>
                  </div>
                </div>

                {/* Bio */}
                <p className="text-gray-600 text-sm mb-4 line-clamp-3">{consultant.bio}</p>

                {/* Skills */}
                <div className="flex flex-wrap gap-1 mb-4">
                  {consultant.skills.slice(0, 4).map((skill, index) => (
                    <span key={index} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                      {skill}
                    </span>
                  ))}
                  {consultant.skills.length > 4 && (
                    <span className="text-gray-500 text-xs">+{consultant.skills.length - 4} more</span>
                  )}
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                  <div className="flex items-center space-x-1 text-gray-600">
                    <Briefcase className="w-4 h-4" />
                    <span>{consultant.projects_completed} projects</span>
                  </div>
                  <div className="flex items-center space-x-1 text-gray-600">
                    <Award className="w-4 h-4" />
                    <span>{consultant.experience_years}+ years</span>
                  </div>
                  <div className="flex items-center space-x-1 text-gray-600">
                    <Clock className="w-4 h-4" />
                    <span>{consultant.response_time}</span>
                  </div>
                  <div className="flex items-center space-x-1 text-gray-600">
                    <span className="text-green-600">✓</span>
                    <span>{consultant.success_rate}% success</span>
                  </div>
                </div>

                {/* Availability Status */}
                <div className="mb-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    consultant.availability === 'available' 
                      ? 'bg-green-100 text-green-800' 
                      : consultant.availability === 'busy'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {consultant.availability === 'available' ? 'Available Now' :
                     consultant.availability === 'busy' ? 'Busy' : 'Part-time'}
                  </span>
                </div>

                {/* Price and Actions */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1">
                    <DollarSign className="w-4 h-4 text-gray-600" />
                    <span className="font-semibold text-gray-900">
                      ${consultant.hourly_rate}/hr
                    </span>
                  </div>
                  <div className="flex space-x-2">
                    <Link
                      href={`/consultants/${consultant.id}`}
                      className="text-blue-600 hover:text-blue-500 text-sm font-medium"
                    >
                      View Profile
                    </Link>
                    <button
                      onClick={() => handleHireConsultant(consultant.id)}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                    >
                      Hire Now
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredConsultants.length === 0 && !loading && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg">No consultants found matching your criteria</div>
            <p className="text-gray-400 mt-2">Try adjusting your search or filters</p>
          </div>
        )}
      </div>
    </div>
  );
}
