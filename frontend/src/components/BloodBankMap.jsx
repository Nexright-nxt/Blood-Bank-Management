import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  Building2, Phone, Clock, Droplet, Navigation, 
  Filter, Locate, RefreshCw, ExternalLink 
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent } from './ui/card';

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

// Custom blood bank marker
const createBloodBankIcon = (hasStock, is24x7) => {
  const color = hasStock ? (is24x7 ? '#16a34a' : '#2563eb') : '#94a3b8';
  return L.divIcon({
    className: 'blood-bank-marker',
    html: `
      <div style="
        position: relative;
        width: 36px;
        height: 36px;
      ">
        <div style="
          background-color: ${color};
          width: 32px;
          height: 32px;
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          border: 3px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          <span style="
            transform: rotate(45deg);
            font-size: 14px;
          ">🩸</span>
        </div>
        ${is24x7 ? `<div style="
          position: absolute;
          top: -4px;
          right: -4px;
          background: #16a34a;
          color: white;
          font-size: 8px;
          padding: 1px 3px;
          border-radius: 4px;
          font-weight: bold;
        ">24/7</div>` : ''}
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -36],
  });
};

// User location marker
const userLocationIcon = L.divIcon({
  className: 'user-location-marker',
  html: `
    <div style="
      width: 20px;
      height: 20px;
      background: #3b82f6;
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3), 0 2px 4px rgba(0,0,0,0.3);
    "></div>
  `,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

// Component to fit bounds
function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);
  return null;
}

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function BloodBankMap({ 
  height = '500px',
  initialUserLocation = null,
  onBloodBankSelect = null,
}) {
  const [userLocation, setUserLocation] = useState(initialUserLocation);
  const [bloodBanks, setBloodBanks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [gettingLocation, setGettingLocation] = useState(false);
  const [selectedBloodGroup, setSelectedBloodGroup] = useState('all');
  const [selectedBank, setSelectedBank] = useState(null);
  const mapRef = useRef(null);

  const defaultCenter = [20.5937, 78.9629]; // India center

  // Fetch blood banks when user location changes
  useEffect(() => {
    if (userLocation) {
      fetchBloodBanks();
    }
  }, [userLocation, selectedBloodGroup]);

  const fetchBloodBanks = async () => {
    if (!userLocation) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/blood-link/search`, {
        latitude: userLocation[0],
        longitude: userLocation[1],
        blood_group: selectedBloodGroup === 'all' ? undefined : selectedBloodGroup,
        max_distance_km: 200,
        min_units: 0, // Show all, even with 0 stock
      });
      setBloodBanks(response.data.blood_banks || []);
    } catch (error) {
      toast.error('Failed to fetch blood banks');
    } finally {
      setLoading(false);
    }
  };

  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported by your browser');
      return;
    }
    setGettingLocation(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const newPos = [pos.coords.latitude, pos.coords.longitude];
        setUserLocation(newPos);
        if (mapRef.current) {
          mapRef.current.setView(newPos, 12);
        }
        setGettingLocation(false);
        toast.success('Location detected');
      },
      (error) => {
        setGettingLocation(false);
        toast.error('Unable to get your location');
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const getDirections = (bank) => {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${bank.latitude},${bank.longitude}`;
    window.open(url, '_blank');
  };

  const handleBankClick = (bank) => {
    setSelectedBank(bank);
    if (onBloodBankSelect) {
      onBloodBankSelect(bank);
    }
  };

  // Calculate bounds for all markers
  const getBounds = () => {
    const points = [];
    if (userLocation) points.push(userLocation);
    bloodBanks.forEach(bank => {
      if (bank.latitude && bank.longitude) {
        points.push([bank.latitude, bank.longitude]);
      }
    });
    return points.length > 1 ? points : null;
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <Button
          variant="outline"
          onClick={getCurrentLocation}
          disabled={gettingLocation}
          className="gap-2"
        >
          <Locate className={`w-4 h-4 ${gettingLocation ? 'animate-spin' : ''}`} />
          {gettingLocation ? 'Detecting...' : 'My Location'}
        </Button>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <Select
            value={selectedBloodGroup}
            onValueChange={setSelectedBloodGroup}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Blood Group" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Groups</SelectItem>
              {BLOOD_GROUPS.map(bg => (
                <SelectItem key={bg} value={bg}>{bg}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          variant="outline"
          onClick={fetchBloodBanks}
          disabled={loading || !userLocation}
          className="gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>

        {bloodBanks.length > 0 && (
          <Badge variant="outline" className="ml-auto">
            {bloodBanks.length} blood bank{bloodBanks.length !== 1 ? 's' : ''} found
          </Badge>
        )}
      </div>

      {/* Map and Info Panel */}
      <div className="flex gap-4 flex-col lg:flex-row">
        {/* Map */}
        <div style={{ height }} className="flex-1 rounded-lg overflow-hidden border">
          <MapContainer
            center={userLocation || defaultCenter}
            zoom={userLocation ? 12 : 5}
            style={{ height: '100%', width: '100%' }}
            ref={mapRef}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* User location marker */}
            {userLocation && (
              <Marker position={userLocation} icon={userLocationIcon}>
                <Popup>
                  <strong>Your Location</strong>
                </Popup>
              </Marker>
            )}

            {/* Blood bank markers */}
            {bloodBanks.map(bank => (
              <Marker
                key={bank.org_id}
                position={[bank.latitude, bank.longitude]}
                icon={createBloodBankIcon(bank.total_units > 0, bank.is_24x7)}
                eventHandlers={{
                  click: () => handleBankClick(bank),
                }}
              >
                <Popup>
                  <div className="min-w-[200px]">
                    <strong className="text-base">{bank.org_name}</strong>
                    <p className="text-sm text-slate-600 mt-1">
                      {bank.address}, {bank.city}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge className={bank.total_units > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}>
                        {bank.total_units} units
                      </Badge>
                      <span className="text-sm text-slate-500">{bank.distance_km} km</span>
                    </div>
                    <Button
                      size="sm"
                      className="w-full mt-2"
                      onClick={() => getDirections(bank)}
                    >
                      <Navigation className="w-3 h-3 mr-1" />
                      Get Directions
                    </Button>
                  </div>
                </Popup>
              </Marker>
            ))}

            {/* Fit bounds to show all markers */}
            <FitBounds bounds={getBounds()} />
          </MapContainer>
        </div>

        {/* Selected Bank Info Panel */}
        {selectedBank && (
          <Card className="lg:w-80 flex-shrink-0">
            <CardContent className="p-4 space-y-4">
              <div>
                <div className="flex items-start justify-between">
                  <h3 className="font-semibold text-lg">{selectedBank.org_name}</h3>
                  {selectedBank.is_24x7 && (
                    <Badge className="bg-green-100 text-green-700">24/7</Badge>
                  )}
                </div>
                <p className="text-sm text-slate-600 mt-1">
                  {selectedBank.address}, {selectedBank.city}, {selectedBank.state}
                </p>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-red-600">{selectedBank.total_units}</p>
                  <p className="text-xs text-slate-500">units available</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-slate-700">{selectedBank.distance_km}</p>
                  <p className="text-xs text-slate-500">km away</p>
                </div>
              </div>

              {/* Availability breakdown */}
              {Object.keys(selectedBank.availability || {}).length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Availability:</p>
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(selectedBank.availability).map(([bg, components]) => {
                      const total = Object.values(components).reduce((a, b) => a + b, 0);
                      return (
                        <Badge key={bg} variant="outline" className="text-xs">
                          {bg}: {total}
                        </Badge>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Contact */}
              <div className="space-y-2 text-sm">
                {selectedBank.contact_phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-slate-400" />
                    <a href={`tel:${selectedBank.contact_phone}`} className="text-blue-600 hover:underline">
                      {selectedBank.contact_phone}
                    </a>
                  </div>
                )}
                {selectedBank.operating_hours && (
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <span>{selectedBank.operating_hours}</span>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => getDirections(selectedBank)}
                >
                  <Navigation className="w-4 h-4 mr-1" />
                  Directions
                </Button>
                {selectedBank.contact_phone && (
                  <Button
                    className="flex-1 bg-red-600 hover:bg-red-700"
                    onClick={() => window.location.href = `tel:${selectedBank.contact_phone}`}
                  >
                    <Phone className="w-4 h-4 mr-1" />
                    Call
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
        <span className="font-medium">Legend:</span>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded-full bg-green-600"></div>
          <span>24/7 with stock</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded-full bg-blue-600"></div>
          <span>Has stock</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded-full bg-slate-400"></div>
          <span>No stock</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded-full bg-blue-500 border-2 border-white shadow"></div>
          <span>Your location</span>
        </div>
      </div>
    </div>
  );
}
