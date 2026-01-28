import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  MapPin, Search, Navigation, Phone, Mail, Clock, 
  Droplet, Building2, AlertCircle, RefreshCw, ExternalLink,
  Locate, Filter, X, Megaphone, AlertTriangle, Package, MessageSquare, Map
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Slider } from '../components/ui/slider';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import BloodBankMap from '../components/BloodBankMap';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const COMPONENT_TYPES = [
  { value: 'all', label: 'All Components' },
  { value: 'whole_blood', label: 'Whole Blood' },
  { value: 'prc', label: 'Packed Red Cells' },
  { value: 'ffp', label: 'Fresh Frozen Plasma' },
  { value: 'platelets', label: 'Platelets' },
  { value: 'cryoprecipitate', label: 'Cryoprecipitate' }
];

export default function BloodLinkSearch() {
  const [loading, setLoading] = useState(false);
  const [gettingLocation, setGettingLocation] = useState(false);
  const [results, setResults] = useState(null);
  const [selectedBank, setSelectedBank] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [broadcasts, setBroadcasts] = useState([]);
  const [loadingBroadcasts, setLoadingBroadcasts] = useState(true);
  const [selectedBroadcast, setSelectedBroadcast] = useState(null);
  
  const [searchParams, setSearchParams] = useState({
    latitude: null,
    longitude: null,
    blood_group: 'any',
    component_type: 'all',
    max_distance_km: 50,
    min_units: 1
  });

  // Fetch active broadcasts on mount
  useEffect(() => {
    fetchBroadcasts();
  }, []);

  const fetchBroadcasts = async () => {
    setLoadingBroadcasts(true);
    try {
      const response = await axios.get(`${API_URL}/broadcasts/active`);
      setBroadcasts(response.data.broadcasts || []);
    } catch (error) {
      console.error('Failed to fetch broadcasts:', error);
    } finally {
      setLoadingBroadcasts(false);
    }
  };

  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported by your browser');
      return;
    }

    setGettingLocation(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setSearchParams(prev => ({
          ...prev,
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        }));
        setGettingLocation(false);
        toast.success('Location detected');
      },
      (error) => {
        setGettingLocation(false);
        toast.error('Unable to get your location. Please enter manually.');
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleSearch = async () => {
    if (!searchParams.latitude || !searchParams.longitude) {
      toast.error('Please provide your location');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/blood-link/search`, {
        latitude: parseFloat(searchParams.latitude),
        longitude: parseFloat(searchParams.longitude),
        blood_group: searchParams.blood_group === 'any' ? undefined : searchParams.blood_group,
        component_type: searchParams.component_type === 'all' ? undefined : searchParams.component_type,
        max_distance_km: searchParams.max_distance_km,
        min_units: searchParams.min_units
      });
      setResults(response.data);
      if (response.data.results_count === 0) {
        toast.info('No blood banks found matching your criteria');
      }
    } catch (error) {
      toast.error('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getAvailabilityBadge = (total) => {
    if (total === 0) return <Badge className="bg-red-100 text-red-700">No Stock</Badge>;
    if (total < 5) return <Badge className="bg-yellow-100 text-yellow-700">Low Stock</Badge>;
    return <Badge className="bg-green-100 text-green-700">Available</Badge>;
  };

  const formatAvailability = (availability) => {
    const items = [];
    for (const [bloodGroup, components] of Object.entries(availability)) {
      for (const [compType, count] of Object.entries(components)) {
        items.push({ bloodGroup, compType, count });
      }
    }
    return items;
  };

  const getPriorityStyles = (priority) => {
    switch (priority) {
      case 'critical':
        return 'border-red-500 bg-red-50';
      case 'high':
        return 'border-orange-400 bg-orange-50';
      default:
        return 'border-slate-200 bg-white';
    }
  };

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'critical':
        return <Badge className="bg-red-600 text-white">Critical</Badge>;
      case 'high':
        return <Badge className="bg-orange-500 text-white">High Priority</Badge>;
      default:
        return <Badge variant="outline">Normal</Badge>;
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-rose-100 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Droplet className="w-8 h-8 text-red-600" />
            <h1 className="text-3xl font-bold text-slate-800">Blood Link</h1>
          </div>
          <p className="text-slate-600">Find nearby blood banks with available stock</p>
        </div>

        {/* Network Alerts Section */}
        {broadcasts.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <Megaphone className="w-5 h-5 text-red-600" />
              <h2 className="font-semibold text-slate-800">Network Alerts</h2>
              <Badge variant="outline" className="ml-auto">
                {broadcasts.length} active
              </Badge>
            </div>
            <div className="space-y-3">
              {broadcasts.slice(0, 3).map((broadcast) => (
                <Card 
                  key={broadcast.id}
                  className={`border-l-4 cursor-pointer hover:shadow-md transition-shadow ${getPriorityStyles(broadcast.priority)}`}
                  onClick={() => setSelectedBroadcast(broadcast)}
                  data-testid={`broadcast-${broadcast.id}`}
                >
                  <CardContent className="py-3">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        {broadcast.broadcast_type === 'urgent_need' ? (
                          <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                        ) : (
                          <Package className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                        )}
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium text-slate-800">{broadcast.title}</span>
                            {getPriorityBadge(broadcast.priority)}
                            <Badge className={broadcast.broadcast_type === 'urgent_need' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}>
                              {broadcast.blood_group}
                            </Badge>
                          </div>
                          <p className="text-sm text-slate-600 mt-1">
                            {broadcast.org_name} • {formatTimeAgo(broadcast.created_at)}
                            {broadcast.units_needed && ` • ${broadcast.units_needed} units needed`}
                            {broadcast.units_available && ` • ${broadcast.units_available} units available`}
                          </p>
                        </div>
                      </div>
                      <Badge variant="outline" className="flex-shrink-0">
                        {broadcast.broadcast_type === 'urgent_need' ? 'Need' : 'Surplus'}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
              {broadcasts.length > 3 && (
                <Button variant="ghost" className="w-full text-slate-600" onClick={() => setSelectedBroadcast(broadcasts[0])}>
                  View all {broadcasts.length} alerts
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Search Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5" />
              Search for Blood
            </CardTitle>
            <CardDescription>
              Enter your location and blood requirements to find nearby blood banks
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Location Input */}
            <div className="space-y-2">
              <Label>Your Location</Label>
              <div className="flex gap-2">
                <div className="flex-1 grid grid-cols-2 gap-2">
                  <Input
                    type="number"
                    step="any"
                    placeholder="Latitude"
                    value={searchParams.latitude || ''}
                    onChange={(e) => setSearchParams(prev => ({ ...prev, latitude: e.target.value }))}
                    data-testid="latitude-input"
                  />
                  <Input
                    type="number"
                    step="any"
                    placeholder="Longitude"
                    value={searchParams.longitude || ''}
                    onChange={(e) => setSearchParams(prev => ({ ...prev, longitude: e.target.value }))}
                    data-testid="longitude-input"
                  />
                </div>
                <Button
                  variant="outline"
                  onClick={getCurrentLocation}
                  disabled={gettingLocation}
                  data-testid="detect-location-btn"
                >
                  {gettingLocation ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Locate className="w-4 h-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-slate-500">
                Click the location button to auto-detect your coordinates
              </p>
            </div>

            {/* Quick Filters */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <Label>Blood Group</Label>
                <Select
                  value={searchParams.blood_group}
                  onValueChange={(v) => setSearchParams(prev => ({ ...prev, blood_group: v }))}
                >
                  <SelectTrigger data-testid="blood-group-select">
                    <SelectValue placeholder="Any" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="any">Any Blood Group</SelectItem>
                    {BLOOD_GROUPS.map((bg) => (
                      <SelectItem key={bg} value={bg}>{bg}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Component Type</Label>
                <Select
                  value={searchParams.component_type}
                  onValueChange={(v) => setSearchParams(prev => ({ ...prev, component_type: v }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="All" />
                  </SelectTrigger>
                  <SelectContent>
                    {COMPONENT_TYPES.map((ct) => (
                      <SelectItem key={ct.value} value={ct.value}>{ct.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Search Radius</Label>
                <Select
                  value={String(searchParams.max_distance_km)}
                  onValueChange={(v) => setSearchParams(prev => ({ ...prev, max_distance_km: parseInt(v) }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10 km</SelectItem>
                    <SelectItem value="25">25 km</SelectItem>
                    <SelectItem value="50">50 km</SelectItem>
                    <SelectItem value="100">100 km</SelectItem>
                    <SelectItem value="200">200 km</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Search Button */}
            <Button 
              className="w-full bg-red-600 hover:bg-red-700"
              onClick={handleSearch}
              disabled={loading || !searchParams.latitude || !searchParams.longitude}
              data-testid="search-btn"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Search className="w-4 h-4 mr-2" />
              )}
              Search Blood Banks
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        {results && (
          <div className="space-y-4">
            {/* Results Header */}
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-800">
                {results.results_count} Blood Bank{results.results_count !== 1 ? 's' : ''} Found
              </h2>
              {results.filters.blood_group && (
                <Badge variant="outline">{results.filters.blood_group}</Badge>
              )}
            </div>

            {/* Blood Banks List */}
            {results.blood_banks.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <AlertCircle className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-600 mb-2">No blood banks found</p>
                  <p className="text-sm text-slate-500">
                    Try increasing the search radius or removing filters
                  </p>
                </CardContent>
              </Card>
            ) : (
              results.blood_banks.map((bank) => (
                <Card 
                  key={bank.org_id} 
                  className="hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => setSelectedBank(bank)}
                  data-testid={`blood-bank-${bank.org_id}`}
                >
                  <CardContent className="py-4">
                    <div className="flex flex-col sm:flex-row justify-between gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Building2 className="w-5 h-5 text-red-600" />
                          <h3 className="font-semibold text-slate-800">{bank.org_name}</h3>
                          {bank.is_24x7 && (
                            <Badge className="bg-green-100 text-green-700">24x7</Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-1 text-sm text-slate-600">
                          <MapPin className="w-4 h-4" />
                          {bank.address}, {bank.city}, {bank.state}
                        </div>
                        <div className="flex items-center gap-4 text-sm">
                          <span className="flex items-center gap-1 text-slate-500">
                            <Navigation className="w-4 h-4" />
                            {bank.distance_km} km away
                          </span>
                          {bank.contact_phone && (
                            <span className="flex items-center gap-1 text-slate-500">
                              <Phone className="w-4 h-4" />
                              {bank.contact_phone}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        {getAvailabilityBadge(bank.total_units)}
                        <span className="text-2xl font-bold text-red-600">
                          {bank.total_units} units
                        </span>
                        {bank.operating_hours && (
                          <span className="text-xs text-slate-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {bank.operating_hours}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Availability Preview */}
                    {Object.keys(bank.availability).length > 0 && (
                      <div className="mt-4 pt-4 border-t">
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(bank.availability).slice(0, 4).map(([bg, components]) => {
                            const total = Object.values(components).reduce((a, b) => a + b, 0);
                            return (
                              <Badge key={bg} variant="outline" className="text-red-600 border-red-200">
                                {bg}: {total} units
                              </Badge>
                            );
                          })}
                          {Object.keys(bank.availability).length > 4 && (
                            <Badge variant="outline">
                              +{Object.keys(bank.availability).length - 4} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        )}

        {/* Blood Bank Detail Dialog */}
        <Dialog open={!!selectedBank} onOpenChange={() => setSelectedBank(null)}>
          <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-red-600" />
                {selectedBank?.org_name}
              </DialogTitle>
              <DialogDescription>
                {selectedBank?.distance_km} km from your location
              </DialogDescription>
            </DialogHeader>
            {selectedBank && (
              <div className="space-y-4">
                {/* Contact Info */}
                <div className="bg-slate-50 rounded-lg p-4 space-y-2">
                  <div className="flex items-start gap-2">
                    <MapPin className="w-4 h-4 text-slate-500 mt-0.5" />
                    <div>
                      <p className="text-sm">{selectedBank.address}</p>
                      <p className="text-sm text-slate-500">
                        {selectedBank.city}, {selectedBank.state} {selectedBank.pincode}
                      </p>
                    </div>
                  </div>
                  {selectedBank.contact_phone && (
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-slate-500" />
                      <a href={`tel:${selectedBank.contact_phone}`} className="text-sm text-blue-600 hover:underline">
                        {selectedBank.contact_phone}
                      </a>
                    </div>
                  )}
                  {selectedBank.contact_email && (
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-slate-500" />
                      <a href={`mailto:${selectedBank.contact_email}`} className="text-sm text-blue-600 hover:underline">
                        {selectedBank.contact_email}
                      </a>
                    </div>
                  )}
                  {selectedBank.operating_hours && (
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-slate-500" />
                      <span className="text-sm">{selectedBank.operating_hours}</span>
                      {selectedBank.is_24x7 && (
                        <Badge className="bg-green-100 text-green-700 text-xs">24x7</Badge>
                      )}
                    </div>
                  )}
                </div>

                {/* Availability */}
                <div>
                  <h4 className="font-medium mb-3 flex items-center gap-2">
                    <Droplet className="w-4 h-4 text-red-600" />
                    Blood Availability
                  </h4>
                  {Object.keys(selectedBank.availability).length === 0 ? (
                    <p className="text-sm text-slate-500 text-center py-4">
                      No blood currently available
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {Object.entries(selectedBank.availability).map(([bg, components]) => (
                        <div key={bg} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                          <span className="font-medium text-red-600">{bg}</span>
                          <div className="flex gap-2">
                            {Object.entries(components).map(([type, count]) => (
                              <Badge key={type} variant="outline" className="text-xs">
                                {type.replace('_', ' ')}: {count}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-4 border-t">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => {
                      const url = `https://www.google.com/maps/dir/?api=1&destination=${selectedBank.latitude},${selectedBank.longitude}`;
                      window.open(url, '_blank');
                    }}
                  >
                    <Navigation className="w-4 h-4 mr-2" />
                    Get Directions
                  </Button>
                  {selectedBank.contact_phone && (
                    <Button
                      className="flex-1 bg-red-600 hover:bg-red-700"
                      onClick={() => window.location.href = `tel:${selectedBank.contact_phone}`}
                    >
                      <Phone className="w-4 h-4 mr-2" />
                      Call Now
                    </Button>
                  )}
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Broadcast Detail Dialog */}
        <Dialog open={!!selectedBroadcast} onOpenChange={() => setSelectedBroadcast(null)}>
          <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                {selectedBroadcast?.broadcast_type === 'urgent_need' ? (
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                ) : (
                  <Package className="w-5 h-5 text-green-600" />
                )}
                {selectedBroadcast?.title}
              </DialogTitle>
              <DialogDescription>
                {selectedBroadcast?.broadcast_type === 'urgent_need' ? 'Urgent Blood Need' : 'Surplus Blood Alert'}
                {' '} from {selectedBroadcast?.org_name}
              </DialogDescription>
            </DialogHeader>
            {selectedBroadcast && (
              <div className="space-y-4">
                {/* Priority & Type */}
                <div className="flex items-center gap-2 flex-wrap">
                  {getPriorityBadge(selectedBroadcast.priority)}
                  <Badge className={selectedBroadcast.broadcast_type === 'urgent_need' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}>
                    {selectedBroadcast.blood_group}
                  </Badge>
                  {selectedBroadcast.component_type && (
                    <Badge variant="outline">{selectedBroadcast.component_type.replace('_', ' ')}</Badge>
                  )}
                </div>

                {/* Details */}
                <div className="bg-slate-50 rounded-lg p-4 space-y-3">
                  {selectedBroadcast.broadcast_type === 'urgent_need' && selectedBroadcast.units_needed && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-600">Units Needed:</span>
                      <span className="font-semibold text-red-600">{selectedBroadcast.units_needed}</span>
                    </div>
                  )}
                  {selectedBroadcast.broadcast_type === 'surplus_alert' && selectedBroadcast.units_available && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-600">Units Available:</span>
                      <span className="font-semibold text-green-600">{selectedBroadcast.units_available}</span>
                    </div>
                  )}
                  {selectedBroadcast.expiry_date && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-600">Expiry Date:</span>
                      <span className="font-medium">{new Date(selectedBroadcast.expiry_date).toLocaleDateString()}</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600">Posted:</span>
                    <span className="text-sm">{formatTimeAgo(selectedBroadcast.created_at)}</span>
                  </div>
                  {selectedBroadcast.response_count > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-600">Responses:</span>
                      <Badge variant="outline">{selectedBroadcast.response_count}</Badge>
                    </div>
                  )}
                </div>

                {/* Description */}
                {selectedBroadcast.description && (
                  <div>
                    <p className="text-sm text-slate-500 mb-1">Details:</p>
                    <p className="text-slate-700">{selectedBroadcast.description}</p>
                  </div>
                )}

                {/* Contact Info */}
                <div className="border-t pt-4 space-y-2">
                  <p className="text-sm font-medium text-slate-700">Contact Information</p>
                  <div className="flex items-center gap-2 text-slate-600">
                    <Building2 className="w-4 h-4" />
                    <span>{selectedBroadcast.org_name}</span>
                  </div>
                  {selectedBroadcast.contact_name && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <MessageSquare className="w-4 h-4" />
                      <span>{selectedBroadcast.contact_name}</span>
                    </div>
                  )}
                  {selectedBroadcast.contact_phone && (
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-slate-500" />
                      <a href={`tel:${selectedBroadcast.contact_phone}`} className="text-blue-600 hover:underline">
                        {selectedBroadcast.contact_phone}
                      </a>
                    </div>
                  )}
                </div>

                {/* Action */}
                {selectedBroadcast.contact_phone && (
                  <Button
                    className="w-full bg-red-600 hover:bg-red-700"
                    onClick={() => window.location.href = `tel:${selectedBroadcast.contact_phone}`}
                  >
                    <Phone className="w-4 h-4 mr-2" />
                    Contact Blood Bank
                  </Button>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Emergency Info */}
        <Card className="mt-6 border-red-200 bg-red-50">
          <CardContent className="py-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div>
                <p className="font-medium text-red-800">Emergency?</p>
                <p className="text-sm text-red-600">
                  For emergencies, call your nearest hospital or blood bank directly. 
                  Availability shown here may not reflect real-time stock.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
