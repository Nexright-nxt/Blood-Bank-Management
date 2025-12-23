import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { donorAPI, screeningAPI } from '../lib/api';
import { toast } from 'sonner';
import { Search, Clipboard, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';

const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function Screening() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [donor, setDonor] = useState(null);
  const [eligibility, setEligibility] = useState(null);
  const [showResultDialog, setShowResultDialog] = useState(false);
  const [screeningResult, setScreeningResult] = useState(null);

  const [formData, setFormData] = useState({
    screening_date: new Date().toISOString().split('T')[0],
    weight: '',
    height: '',
    blood_pressure_systolic: '',
    blood_pressure_diastolic: '',
    pulse: '',
    temperature: '',
    hemoglobin: '',
    preliminary_blood_group: '',
    questionnaire_passed: false,
  });

  useEffect(() => {
    const donorId = searchParams.get('donor');
    if (donorId) {
      fetchDonor(donorId);
    }
  }, [searchParams]);

  const fetchDonor = async (id) => {
    try {
      const [donorRes, eligibilityRes] = await Promise.all([
        donorAPI.getById(id),
        donorAPI.checkEligibility(id)
      ]);
      setDonor(donorRes.data);
      setEligibility(eligibilityRes.data);
      if (donorRes.data.blood_group) {
        setFormData(prev => ({ ...prev, preliminary_blood_group: donorRes.data.blood_group }));
      }
    } catch (error) {
      toast.error('Failed to fetch donor');
    }
  };

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;
    
    setLoading(true);
    try {
      const response = await donorAPI.getAll({ search: searchTerm });
      if (response.data.length === 0) {
        toast.error('No donor found');
      } else if (response.data.length === 1) {
        fetchDonor(response.data[0].id);
      } else {
        toast.info(`Found ${response.data.length} donors. Please be more specific.`);
      }
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!donor) {
      toast.error('Please select a donor first');
      return;
    }

    setLoading(true);
    try {
      const response = await screeningAPI.create({
        ...formData,
        donor_id: donor.id,
        weight: parseFloat(formData.weight),
        height: parseFloat(formData.height),
        blood_pressure_systolic: parseInt(formData.blood_pressure_systolic),
        blood_pressure_diastolic: parseInt(formData.blood_pressure_diastolic),
        pulse: parseInt(formData.pulse),
        temperature: parseFloat(formData.temperature),
        hemoglobin: parseFloat(formData.hemoglobin),
      });
      
      setScreeningResult(response.data);
      setShowResultDialog(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit screening');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="screening-page">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Health Screening</h1>
        <p className="page-subtitle">Pre-donation health assessment and eligibility check</p>
      </div>

      {/* Donor Search */}
      {!donor && (
        <Card>
          <CardHeader>
            <CardTitle>Find Donor</CardTitle>
            <CardDescription>Search by donor ID, name, or phone number</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Enter donor ID, name, or phone..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  className="pl-9"
                  data-testid="donor-search"
                />
              </div>
              <Button onClick={handleSearch} disabled={loading} data-testid="search-btn">
                Search
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Selected Donor */}
      {donor && (
        <Card className={`border-l-4 ${eligibility?.eligible ? 'border-l-emerald-500' : 'border-l-red-500'}`}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  eligibility?.eligible ? 'bg-emerald-100' : 'bg-red-100'
                }`}>
                  {eligibility?.eligible ? (
                    <CheckCircle className="w-6 h-6 text-emerald-600" />
                  ) : (
                    <XCircle className="w-6 h-6 text-red-600" />
                  )}
                </div>
                <div>
                  <p className="font-semibold">{donor.full_name}</p>
                  <p className="text-sm text-slate-500 font-mono">{donor.donor_id}</p>
                </div>
                {donor.blood_group && (
                  <span className="blood-group-badge ml-4">{donor.blood_group}</span>
                )}
              </div>
              <Button variant="outline" onClick={() => setDonor(null)} data-testid="change-donor-btn">
                Change Donor
              </Button>
            </div>
            {!eligibility?.eligible && eligibility?.issues && (
              <div className="mt-4 p-3 bg-red-50 rounded-lg">
                <p className="text-sm font-medium text-red-700 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Eligibility Issues:
                </p>
                <ul className="text-sm text-red-600 list-disc ml-6 mt-1">
                  {eligibility.issues.map((issue, idx) => (
                    <li key={idx}>{issue}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Screening Form */}
      {donor && eligibility?.eligible && (
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Vitals */}
            <Card className="form-section">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clipboard className="w-5 h-5 text-teal-600" />
                  Vital Signs
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="weight">Weight (kg) *</Label>
                    <Input
                      id="weight"
                      type="number"
                      step="0.1"
                      value={formData.weight}
                      onChange={(e) => handleChange('weight', e.target.value)}
                      placeholder="e.g., 65"
                      required
                      data-testid="input-weight"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="height">Height (cm) *</Label>
                    <Input
                      id="height"
                      type="number"
                      step="0.1"
                      value={formData.height}
                      onChange={(e) => handleChange('height', e.target.value)}
                      placeholder="e.g., 170"
                      required
                      data-testid="input-height"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="bp_systolic">BP Systolic (mmHg) *</Label>
                    <Input
                      id="bp_systolic"
                      type="number"
                      value={formData.blood_pressure_systolic}
                      onChange={(e) => handleChange('blood_pressure_systolic', e.target.value)}
                      placeholder="e.g., 120"
                      required
                      data-testid="input-bp-systolic"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bp_diastolic">BP Diastolic (mmHg) *</Label>
                    <Input
                      id="bp_diastolic"
                      type="number"
                      value={formData.blood_pressure_diastolic}
                      onChange={(e) => handleChange('blood_pressure_diastolic', e.target.value)}
                      placeholder="e.g., 80"
                      required
                      data-testid="input-bp-diastolic"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="pulse">Pulse (bpm) *</Label>
                    <Input
                      id="pulse"
                      type="number"
                      value={formData.pulse}
                      onChange={(e) => handleChange('pulse', e.target.value)}
                      placeholder="e.g., 72"
                      required
                      data-testid="input-pulse"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="temperature">Temperature (°C) *</Label>
                    <Input
                      id="temperature"
                      type="number"
                      step="0.1"
                      value={formData.temperature}
                      onChange={(e) => handleChange('temperature', e.target.value)}
                      placeholder="e.g., 36.5"
                      required
                      data-testid="input-temperature"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Blood Test */}
            <Card className="form-section">
              <CardHeader>
                <CardTitle>Blood Assessment</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="hemoglobin">Hemoglobin (g/dL) *</Label>
                  <Input
                    id="hemoglobin"
                    type="number"
                    step="0.1"
                    value={formData.hemoglobin}
                    onChange={(e) => handleChange('hemoglobin', e.target.value)}
                    placeholder="e.g., 14.0"
                    required
                    data-testid="input-hemoglobin"
                  />
                  <p className="text-xs text-slate-500">Minimum: 12.5 g/dL</p>
                </div>
                <div className="space-y-2">
                  <Label>Preliminary Blood Group</Label>
                  <Select 
                    value={formData.preliminary_blood_group} 
                    onValueChange={(v) => handleChange('preliminary_blood_group', v)}
                  >
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
                <div className="pt-4 border-t">
                  <div className="flex items-start gap-3">
                    <Checkbox
                      id="questionnaire"
                      checked={formData.questionnaire_passed}
                      onCheckedChange={(checked) => handleChange('questionnaire_passed', checked)}
                      data-testid="checkbox-questionnaire"
                    />
                    <div className="grid gap-1.5 leading-none">
                      <label htmlFor="questionnaire" className="text-sm font-medium cursor-pointer">
                        Health Questionnaire Passed *
                      </label>
                      <p className="text-sm text-slate-500">
                        Donor has completed and passed all health questionnaire requirements
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-end gap-4 mt-6">
            <Button type="button" variant="outline" onClick={() => navigate('/donors')}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              className="bg-teal-600 hover:bg-teal-700"
              disabled={loading || !formData.questionnaire_passed}
              data-testid="submit-screening-btn"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
              ) : null}
              Submit Screening
            </Button>
          </div>
        </form>
      )}

      {/* Result Dialog */}
      <Dialog open={showResultDialog} onOpenChange={setShowResultDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {screeningResult?.eligibility_status === 'eligible' ? (
                <><CheckCircle className="w-5 h-5 text-emerald-600" /> Screening Passed</>
              ) : (
                <><XCircle className="w-5 h-5 text-red-600" /> Screening Failed</>
              )}
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            {screeningResult?.eligibility_status === 'eligible' ? (
              <p className="text-slate-600">
                Donor is eligible to donate blood. Proceed to the Collection module.
              </p>
            ) : (
              <div>
                <p className="text-slate-600 mb-2">Donor is not eligible due to:</p>
                <p className="text-red-600 text-sm">{screeningResult?.rejection_reason}</p>
              </div>
            )}
          </div>
          <DialogFooter>
            {screeningResult?.eligibility_status === 'eligible' ? (
              <Button 
                onClick={() => navigate(`/collection?donor=${donor.id}&screening=${screeningResult.screening_id}`)}
                className="bg-teal-600 hover:bg-teal-700"
              >
                Proceed to Collection
              </Button>
            ) : (
              <Button variant="outline" onClick={() => setShowResultDialog(false)}>
                Close
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
