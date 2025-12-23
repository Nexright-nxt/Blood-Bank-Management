import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { donorAPI } from '../lib/api';
import { toast } from 'sonner';
import { ArrowLeft, Save, User, Phone, MapPin, CreditCard } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Textarea } from '../components/ui/textarea';

const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const genders = ['Male', 'Female', 'Other'];
const identityTypes = ['Aadhar', 'Passport', 'Driving License', 'Voter ID', 'PAN Card'];

export default function DonorRegistration() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    full_name: '',
    date_of_birth: '',
    gender: '',
    blood_group: '',
    phone: '',
    email: '',
    address: '',
    identity_type: '',
    identity_number: '',
    consent_given: false,
    registration_channel: 'on_site',
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const validateStep = (stepNum) => {
    switch (stepNum) {
      case 1:
        return formData.full_name && formData.date_of_birth && formData.gender;
      case 2:
        return formData.phone && formData.address;
      case 3:
        return formData.identity_type && formData.identity_number && formData.consent_given;
      default:
        return true;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.consent_given) {
      toast.error('Donor must provide consent to proceed');
      return;
    }

    setLoading(true);
    try {
      const response = await donorAPI.create(formData);
      toast.success(`Donor registered successfully! ID: ${response.data.donor_id}`);
      navigate('/donors');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to register donor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in" data-testid="donor-registration">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/donors')} data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="page-title">Register New Donor</h1>
          <p className="page-subtitle">Step {step} of 3 - Fill in donor details</p>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-2">
        {[1, 2, 3].map((s) => (
          <React.Fragment key={s}>
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-medium transition-colors ${
                step === s
                  ? 'bg-teal-600 text-white'
                  : step > s
                  ? 'bg-teal-100 text-teal-700'
                  : 'bg-slate-100 text-slate-400'
              }`}
            >
              {s}
            </div>
            {s < 3 && (
              <div className={`w-16 h-1 rounded ${step > s ? 'bg-teal-600' : 'bg-slate-200'}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        {/* Step 1: Personal Information */}
        {step === 1 && (
          <Card className="form-section">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5 text-teal-600" />
                Personal Information
              </CardTitle>
              <CardDescription>Basic details about the donor</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name *</Label>
                  <Input
                    id="full_name"
                    value={formData.full_name}
                    onChange={(e) => handleChange('full_name', e.target.value)}
                    placeholder="Enter full name"
                    required
                    data-testid="input-full-name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="date_of_birth">Date of Birth *</Label>
                  <Input
                    id="date_of_birth"
                    type="date"
                    value={formData.date_of_birth}
                    onChange={(e) => handleChange('date_of_birth', e.target.value)}
                    required
                    data-testid="input-dob"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Gender *</Label>
                  <Select value={formData.gender} onValueChange={(v) => handleChange('gender', v)}>
                    <SelectTrigger data-testid="select-gender">
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>
                    <SelectContent>
                      {genders.map(g => (
                        <SelectItem key={g} value={g}>{g}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Blood Group (if known)</Label>
                  <Select value={formData.blood_group} onValueChange={(v) => handleChange('blood_group', v)}>
                    <SelectTrigger data-testid="select-blood-group">
                      <SelectValue placeholder="Select blood group" />
                    </SelectTrigger>
                    <SelectContent>
                      {bloodGroups.map(bg => (
                        <SelectItem key={bg} value={bg}>{bg}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Contact Information */}
        {step === 2 && (
          <Card className="form-section">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Phone className="w-5 h-5 text-teal-600" />
                Contact Information
              </CardTitle>
              <CardDescription>How to reach the donor</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number *</Label>
                  <Input
                    id="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => handleChange('phone', e.target.value)}
                    placeholder="Enter phone number"
                    required
                    data-testid="input-phone"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email (Optional)</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleChange('email', e.target.value)}
                    placeholder="Enter email address"
                    data-testid="input-email"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="address">Address *</Label>
                <Textarea
                  id="address"
                  value={formData.address}
                  onChange={(e) => handleChange('address', e.target.value)}
                  placeholder="Enter full address"
                  rows={3}
                  required
                  data-testid="input-address"
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Identity & Consent */}
        {step === 3 && (
          <Card className="form-section">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-teal-600" />
                Identity & Consent
              </CardTitle>
              <CardDescription>Verification and legal consent</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Identity Type *</Label>
                  <Select value={formData.identity_type} onValueChange={(v) => handleChange('identity_type', v)}>
                    <SelectTrigger data-testid="select-identity-type">
                      <SelectValue placeholder="Select ID type" />
                    </SelectTrigger>
                    <SelectContent>
                      {identityTypes.map(it => (
                        <SelectItem key={it} value={it}>{it}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="identity_number">Identity Number *</Label>
                  <Input
                    id="identity_number"
                    value={formData.identity_number}
                    onChange={(e) => handleChange('identity_number', e.target.value)}
                    placeholder="Enter ID number"
                    required
                    data-testid="input-identity-number"
                  />
                </div>
              </div>
              <div className="pt-4 border-t">
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="consent"
                    checked={formData.consent_given}
                    onCheckedChange={(checked) => handleChange('consent_given', checked)}
                    data-testid="checkbox-consent"
                  />
                  <div className="grid gap-1.5 leading-none">
                    <label
                      htmlFor="consent"
                      className="text-sm font-medium cursor-pointer"
                    >
                      I consent to donate blood *
                    </label>
                    <p className="text-sm text-slate-500">
                      By checking this box, the donor confirms they understand the blood donation process
                      and consent to have their blood collected and used for medical purposes.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Navigation Buttons */}
        <div className="flex justify-between pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => setStep(step - 1)}
            disabled={step === 1}
            data-testid="prev-step-btn"
          >
            Previous
          </Button>
          
          {step < 3 ? (
            <Button
              type="button"
              onClick={() => setStep(step + 1)}
              disabled={!validateStep(step)}
              className="bg-teal-600 hover:bg-teal-700"
              data-testid="next-step-btn"
            >
              Next Step
            </Button>
          ) : (
            <Button
              type="submit"
              disabled={loading || !validateStep(3)}
              className="bg-teal-600 hover:bg-teal-700"
              data-testid="submit-btn"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              Register Donor
            </Button>
          )}
        </div>
      </form>
    </div>
  );
}
