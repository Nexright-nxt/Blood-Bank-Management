import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Search, MapPin, Locate, Navigation } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icons
const createCustomIcon = (color) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background-color: ${color};
      width: 24px;
      height: 24px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      border: 2px solid white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
    popupAnchor: [0, -24],
  });
};

export const redIcon = createCustomIcon('#dc2626');
export const greenIcon = createCustomIcon('#16a34a');
export const blueIcon = createCustomIcon('#2563eb');
export const orangeIcon = createCustomIcon('#ea580c');

// Component to handle map clicks
function LocationMarker({ position, setPosition, draggable = true }) {
  const map = useMapEvents({
    click(e) {
      setPosition([e.latlng.lat, e.latlng.lng]);
    },
  });

  return position ? (
    <Marker
      position={position}
      icon={redIcon}
      draggable={draggable}
      eventHandlers={{
        dragend: (e) => {
          const marker = e.target;
          const pos = marker.getLatLng();
          setPosition([pos.lat, pos.lng]);
        },
      }}
    >
      <Popup>
        Selected Location<br />
        Lat: {position[0].toFixed(6)}<br />
        Lng: {position[1].toFixed(6)}
      </Popup>
    </Marker>
  ) : null;
}

// Component to recenter map
function RecenterMap({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, map.getZoom());
    }
  }, [center, map]);
  return null;
}

// Address search using Nominatim (OpenStreetMap geocoding)
async function searchAddress(query) {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`
    );
    const data = await response.json();
    return data.map(item => ({
      display_name: item.display_name,
      lat: parseFloat(item.lat),
      lon: parseFloat(item.lon),
    }));
  } catch (error) {
    console.error('Geocoding error:', error);
    return [];
  }
}

// Reverse geocoding
async function reverseGeocode(lat, lon) {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`
    );
    const data = await response.json();
    return data.display_name || null;
  } catch (error) {
    console.error('Reverse geocoding error:', error);
    return null;
  }
}

/**
 * MapPicker - A reusable map component for selecting locations
 */
export function MapPicker({ 
  initialPosition = null, 
  onLocationChange, 
  height = '300px',
  showSearch = true,
  showCurrentLocation = true,
  showCoordinates = true,
}) {
  const [position, setPosition] = useState(initialPosition);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [gettingLocation, setGettingLocation] = useState(false);
  const [address, setAddress] = useState('');
  const mapRef = useRef(null);

  // Default center (can be customized)
  const defaultCenter = [20.5937, 78.9629]; // India center

  useEffect(() => {
    if (position && onLocationChange) {
      onLocationChange({
        latitude: position[0],
        longitude: position[1],
      });
      // Get address for the position
      reverseGeocode(position[0], position[1]).then(addr => {
        if (addr) setAddress(addr);
      });
    }
  }, [position, onLocationChange]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    const results = await searchAddress(searchQuery);
    setSearchResults(results);
    setSearching(false);
  };

  const selectSearchResult = (result) => {
    const newPos = [result.lat, result.lon];
    setPosition(newPos);
    setSearchResults([]);
    setSearchQuery('');
    setAddress(result.display_name);
    if (mapRef.current) {
      mapRef.current.setView(newPos, 15);
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
        setPosition(newPos);
        if (mapRef.current) {
          mapRef.current.setView(newPos, 15);
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

  return (
    <div className="space-y-3">
      {/* Search Bar */}
      {showSearch && (
        <div className="relative">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Input
                placeholder="Search for an address..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pr-10"
                data-testid="map-search-input"
              />
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            </div>
            <Button 
              type="button" 
              variant="outline" 
              onClick={handleSearch}
              disabled={searching}
            >
              {searching ? 'Searching...' : 'Search'}
            </Button>
            {showCurrentLocation && (
              <Button
                type="button"
                variant="outline"
                onClick={getCurrentLocation}
                disabled={gettingLocation}
                title="Use current location"
              >
                <Locate className={`w-4 h-4 ${gettingLocation ? 'animate-spin' : ''}`} />
              </Button>
            )}
          </div>
          
          {/* Search Results Dropdown */}
          {searchResults.length > 0 && (
            <div className="absolute z-[1000] w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-y-auto">
              {searchResults.map((result, index) => (
                <button
                  key={index}
                  type="button"
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-100 border-b last:border-b-0"
                  onClick={() => selectSearchResult(result)}
                >
                  <MapPin className="inline w-4 h-4 mr-2 text-slate-400" />
                  {result.display_name}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Map Container */}
      <div style={{ height }} className="rounded-lg overflow-hidden border">
        <MapContainer
          center={position || defaultCenter}
          zoom={position ? 15 : 5}
          style={{ height: '100%', width: '100%' }}
          ref={mapRef}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <LocationMarker position={position} setPosition={setPosition} />
          {position && <RecenterMap center={position} />}
        </MapContainer>
      </div>

      {/* Selected Location Info */}
      {showCoordinates && position && (
        <div className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg">
          <div className="flex items-start gap-2">
            <MapPin className="w-4 h-4 mt-0.5 text-red-500 flex-shrink-0" />
            <div>
              <p className="font-medium">Selected Location</p>
              {address && <p className="text-xs text-slate-500 mt-1">{address}</p>}
              <p className="text-xs text-slate-400 mt-1">
                Lat: {position[0].toFixed(6)}, Lng: {position[1].toFixed(6)}
              </p>
            </div>
          </div>
        </div>
      )}

      <p className="text-xs text-slate-500">
        Click on the map to select a location, or drag the marker to adjust.
      </p>
    </div>
  );
}

export { searchAddress, reverseGeocode };
export default MapPicker;
