import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  Building2, User, Mail, Phone, MapPin, FileText, 
  ArrowRight, CheckCircle, Loader2, ArrowLeft, Map
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import MapPicker from '../components/MapPicker';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const REQUESTOR_TYPES = [
  { value: 'hospital', label: 'Hospital' },
  { value: 'clinic', label: 'Clinic' },
  { value: 'emergency_service', label: 'Emergency Service' },
  { value: 'research_lab', label: 'Research Laboratory' },
  { value: 'other', label: 'Other' }
];

export default function RequestorRegistration() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    organization_name: '',
    requestor_type: '',
    contact_person: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    address: '',
    city: '',
    state: '',
    pincode: '',
    latitude: null,
    longitude: null,
    license_number: '',
    registration_number: '',
    notes: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSelectChange = (name, value) => {
    setFormData({ ...formData, [name]: value });
  };

  const handleLocationChange = (location) => {
    setFormData({ 
      ...formData, 
      latitude: location.latitude, 
      longitude: location.longitude 
    });
  };

  const validateStep1 = () => {
    if (!formData.organization_name || !formData.requestor_type || !formData.contact_person) {
      toast.error('Please fill in all required fields');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (!formData.email || !formData.phone || !formData.password) {
      toast.error('Please fill in all required fields');
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return false;
    }
    if (formData.password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      toast.error('Please enter a valid email address');
      return false;
    }
    return true;
  };

  const validateStep3 = () => {
    if (!formData.address || !formData.city || !formData.state || !formData.pincode) {
      toast.error('Please fill in all required address fields');
      return false;
    }
    if (!formData.latitude || !formData.longitude) {
      toast.error('Please select your location on the map');
      return false;
    }
    return true;
  };

  const handleNext = () => {
    if (step === 1 && validateStep1()) setStep(2);
    else if (step === 2 && validateStep2()) setStep(3);
    else if (step === 3 && validateStep3()) handleSubmit();
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const submitData = { ...formData };
      delete submitData.confirmPassword;
      
      await axios.post(`${API_URL}/requestors/register`, submitData);
      setSubmitted(true);
      toast.success('Registration submitted successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-rose-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-8 pb-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Registration Submitted!</h2>
            <p className="text-slate-600 mb-6">
              Thank you for registering with Blood Link. Your application is now pending approval.
              You will receive an email notification once your account is approved.
            </p>
            <div className="bg-slate-50 rounded-lg p-4 mb-6">
              <p className="text-sm text-slate-500">Registered Email</p>
              <p className="font-medium text-slate-800">{formData.email}</p>
            </div>
            <div className="space-y-3">
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => navigate('/requestor/check-status')}
              >
                Check Application Status
              </Button>
              <Button 
                className="w-full bg-red-600 hover:bg-red-700"
                onClick={() => navigate('/login')}
              >
                Go to Login
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-rose-100 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <Link to="/login" className="inline-flex items-center text-red-600 hover:text-red-700 mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Login
          </Link>
          <h1 className="text-3xl font-bold text-slate-800">Requestor Registration</h1>
          <p className="text-slate-600 mt-2">
            Register your organization to request blood from Blood Link
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8">
          {[
            { num: 1, label: 'Organization' },
            { num: 2, label: 'Account' },
            { num: 3, label: 'Location' }
          ].map((s, idx) => (
            <React.Fragment key={s.num}>
              <div className="flex flex-col items-center">
                <div 
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                    step >= s.num ? 'bg-red-600 text-white' : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  {s.num}
                </div>
                <span className="text-xs text-slate-500 mt-1">{s.label}</span>
              </div>
              {idx < 2 && (
                <div className={`w-16 h-1 mx-2 mb-4 ${step > s.num ? 'bg-red-600' : 'bg-slate-200'}`} />
              )}
            </React.Fragment>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>
              {step === 1 && 'Organization Information'}
              {step === 2 && 'Account Details'}
              {step === 3 && 'Location & Documents'}
            </CardTitle>
            <CardDescription>
              {step === 1 && 'Tell us about your organization'}
              {step === 2 && 'Create your login credentials'}
              {step === 3 && 'Select your location on the map and provide documents'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Step 1: Organization Info */}
            {step === 1 && (
              <div className="space-y-4">
                <div>
                  <Label htmlFor="organization_name">Organization Name *</Label>
                  <div className="relative mt-1">
                    <Building2 className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <Input
                      id="organization_name"
                      name="organization_name"
                      value={formData.organization_name}
                      onChange={handleChange}
                      className="pl-10"
                      placeholder="Enter organization name"
                      data-testid="org-name-input"
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="requestor_type">Organization Type *</Label>
                  <Select
                    value={formData.requestor_type}
                    onValueChange={(v) => handleSelectChange('requestor_type', v)}
                  >
                    <SelectTrigger data-testid="org-type-select">
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {REQUESTOR_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="contact_person">Contact Person Name *</Label>
                  <div className="relative mt-1">
                    <User className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <Input
                      id="contact_person"
                      name="contact_person"
                      value={formData.contact_person}
                      onChange={handleChange}
                      className="pl-10"
                      placeholder="Full name of contact person"
                      data-testid="contact-person-input"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Account Details */}
            {step === 2 && (
              <div className="space-y-4">
                <div>
                  <Label htmlFor="email">Email Address *</Label>
                  <div className="relative mt-1">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleChange}
                      className="pl-10"
                      placeholder="organization@example.com"
                      data-testid="email-input"
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="phone">Phone Number *</Label>
                  <div className="relative mt-1">
                    <Phone className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <Input
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      className="pl-10"
                      placeholder="+91 XXXXXXXXXX"
                      data-testid="phone-input"
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="password">Password *</Label>
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Minimum 8 characters"
                    data-testid="password-input"
                  />
                </div>
                <div>
                  <Label htmlFor="confirmPassword">Confirm Password *</Label>
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    placeholder="Re-enter password"
                    data-testid="confirm-password-input"
                  />
                </div>
              </div>
            )}

            {/* Step 3: Location & Documents */}
            {step === 3 && (
              <div className="space-y-4">
                {/* Map for location selection */}
                <div>
                  <Label className="flex items-center gap-2 mb-2">
                    <Map className="w-4 h-4" />
                    Select Your Location on Map *
                  </Label>
                  <MapPicker
                    initialPosition={formData.latitude && formData.longitude ? [formData.latitude, formData.longitude] : null}
                    onLocationChange={handleLocationChange}
                    height="300px"
                    showSearch={true}
                    showCurrentLocation={true}
                    showCoordinates={true}
                  />
                </div>

                <div className="border-t pt-4">
                  <h4 className="font-medium text-slate-700 mb-3 flex items-center">
                    <MapPin className="w-4 h-4 mr-2" />
                    Address Details
                  </h4>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="address">Street Address *</Label>
                      <Textarea
                        id="address"
                        name="address"
                        value={formData.address}
                        onChange={handleChange}
                        className="min-h-[60px]"
                        placeholder="Building name, street, area"
                        data-testid="address-input"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="city">City *</Label>
                        <Input
                          id="city"
                          name="city"
                          value={formData.city}
                          onChange={handleChange}
                          placeholder="City"
                          data-testid="city-input"
                        />
                      </div>
                      <div>
                        <Label htmlFor="state">State *</Label>
                        <Input
                          id="state"
                          name="state"
                          value={formData.state}
                          onChange={handleChange}
                          placeholder="State"
                          data-testid="state-input"
                        />
                      </div>
                    </div>
                    <div className="w-1/2">
                      <Label htmlFor="pincode">PIN Code *</Label>
                      <Input
                        id="pincode"
                        name="pincode"
                        value={formData.pincode}
                        onChange={handleChange}
                        placeholder="PIN Code"
                        data-testid="pincode-input"
                      />
                    </div>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h4 className="font-medium text-slate-700 mb-3 flex items-center">
                    <FileText className="w-4 h-4 mr-2" />
                    Optional Documents
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="license_number">License Number</Label>
                      <Input
                        id="license_number"
                        name="license_number"
                        value={formData.license_number}
                        onChange={handleChange}
                        placeholder="Medical license"
                        data-testid="license-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="registration_number">Registration Number</Label>
                      <Input
                        id="registration_number"
                        name="registration_number"
                        value={formData.registration_number}
                        onChange={handleChange}
                        placeholder="Org registration"
                        data-testid="registration-input"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <Label htmlFor="notes">Additional Notes</Label>
                  <Textarea
                    id="notes"
                    name="notes"
                    value={formData.notes}
                    onChange={handleChange}
                    placeholder="Any additional information..."
                    data-testid="notes-input"
                  />
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between mt-6">
              {step > 1 ? (
                <Button variant="outline" onClick={() => setStep(step - 1)}>
                  Back
                </Button>
              ) : (
                <div />
              )}
              <Button 
                onClick={handleNext} 
                disabled={loading}
                className="bg-red-600 hover:bg-red-700"
                data-testid="next-btn"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : null}
                {step === 3 ? 'Submit Registration' : 'Next'}
                {!loading && <ArrowRight className="w-4 h-4 ml-2" />}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Info Box */}
        <div className="mt-6 bg-white/50 rounded-lg p-4 text-sm text-slate-600">
          <p className="font-medium text-slate-700 mb-2">What happens next?</p>
          <ol className="list-decimal list-inside space-y-1">
            <li>Your registration will be reviewed by our team</li>
            <li>You'll receive an email notification once approved</li>
            <li>After approval, you can login and request blood</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
