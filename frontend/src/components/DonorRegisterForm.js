import React, { useState } from 'react';
import { publicDonorAPI } from '../lib/api';
import { toast } from 'sonner';
import { User, Phone, MapPin, CreditCard, CheckCircle, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Checkbox } from './ui/checkbox';
import { Textarea } from './ui/textarea';

const genders = ['Male', 'Female', 'Other'];
const identityTypes = ['Aadhar', 'Passport', 'Driving License', 'Voter ID', 'PAN Card'];

export default function DonorRegisterForm({ onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    full_name: '',
    date_of_birth: '',
    gender: '',
    weight: '',
    phone: '',
    email: '',
    address: '',
    identity_type: '',
    identity_number: '',
    consent_given: false,
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const validateStep = (stepNum) => {
    switch (stepNum) {
      case 1:
        return formData.identity_type && formData.identity_number;
      case 2:
        return formData.full_name && formData.date_of_birth && formData.gender;
      case 3:
        return formData.phone && formData.address && formData.consent_given;
      default:
        return true;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.consent_given) {
      toast.error('You must consent to register as a donor');
      return;
    }

    setLoading(true);
    try {
      const data = {
        ...formData,
        weight: formData.weight ? parseFloat(formData.weight) : undefined,
      };
      
      const response = await publicDonorAPI.register(data);
      toast.success('Registration submitted successfully!');
      onSuccess(response.data.request_id);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-2 mb-6">
        {[1, 2, 3].map((s) => (
          <React.Fragment key={s}>
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                step === s
                  ? 'bg-teal-600 text-white'
                  : step > s
                  ? 'bg-teal-100 text-teal-700'
                  : 'bg-slate-100 text-slate-400'
              }`}
            >
              {step > s ? <CheckCircle className="w-4 h-4" /> : s}
            </div>
            {s < 3 && (
              <div className={`w-8 h-0.5 ${step > s ? 'bg-teal-600' : 'bg-slate-200'}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Step 1: Identity Information */}
      {step === 1 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-2">
            <CreditCard className="w-4 h-4 text-teal-600" />
            Identity Information
          </div>
          
          <div className="space-y-2">
            <Label>Government ID Type *</Label>
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
            <Label htmlFor="identity_number">ID Number *</Label>
            <Input
              id="identity_number"
              value={formData.identity_number}
              onChange={(e) => handleChange('identity_number', e.target.value)}
              placeholder="Enter your ID number"
              required
              data-testid="input-identity-number"
            />
          </div>
        </div>
      )}

      {/* Step 2: Demographics */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-2">
            <User className="w-4 h-4 text-teal-600" />
            Personal Information
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="full_name">Full Name *</Label>
            <Input
              id="full_name"
              value={formData.full_name}
              onChange={(e) => handleChange('full_name', e.target.value)}
              placeholder="Enter your full name"
              required
              data-testid="input-full-name"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
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
            <div className="space-y-2">
              <Label>Gender *</Label>
              <Select value={formData.gender} onValueChange={(v) => handleChange('gender', v)}>
                <SelectTrigger data-testid="select-gender">
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  {genders.map(g => (
                    <SelectItem key={g} value={g}>{g}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="weight">Weight (kg)</Label>
            <Input
              id="weight"
              type="number"
              value={formData.weight}
              onChange={(e) => handleChange('weight', e.target.value)}
              placeholder="e.g., 65"
              data-testid="input-weight"
            />
            <p className="text-xs text-slate-500">Minimum weight for donation: 45 kg</p>
          </div>
        </div>
      )}

      {/* Step 3: Contact & Consent */}
      {step === 3 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-2">
            <Phone className="w-4 h-4 text-teal-600" />
            Contact Information
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number *</Label>
              <Input
                id="phone"
                type="tel"
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                placeholder="Enter phone"
                required
                data-testid="input-phone"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="Enter email"
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
              placeholder="Enter your full address"
              rows={2}
              required
              data-testid="input-address"
            />
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
                  I consent to register as a blood donor *
                </label>
                <p className="text-xs text-slate-500">
                  By checking this box, I confirm that the information provided is accurate 
                  and I consent to be contacted for blood donation purposes.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="flex justify-between pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={() => setStep(step - 1)}
          disabled={step === 1}
        >
          Previous
        </Button>
        
        {step < 3 ? (
          <Button
            type="button"
            onClick={() => setStep(step + 1)}
            disabled={!validateStep(step)}
            className="bg-teal-600 hover:bg-teal-700"
          >
            Next
          </Button>
        ) : (
          <Button
            type="submit"
            disabled={loading || !validateStep(3)}
            className="bg-teal-600 hover:bg-teal-700"
            data-testid="submit-registration-btn"
          >
            {loading ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Submitting...</>
            ) : (
              'Submit Registration'
            )}
          </Button>
        )}
      </div>
    </form>
  );
}
