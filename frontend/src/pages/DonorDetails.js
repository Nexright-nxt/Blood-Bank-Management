import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { donorAPI } from '../lib/api';
import { toast } from 'sonner';
import { ArrowLeft, QrCode, CheckCircle, XCircle, History, Droplet, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

export default function DonorDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [donor, setDonor] = useState(null);
  const [history, setHistory] = useState(null);
  const [eligibility, setEligibility] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDonorData();
  }, [id]);

  const fetchDonorData = async () => {
    try {
      const [donorRes, historyRes, eligibilityRes] = await Promise.all([
        donorAPI.getById(id),
        donorAPI.getHistory(id),
        donorAPI.checkEligibility(id)
      ]);
      setDonor(donorRes.data);
      setHistory(historyRes.data);
      setEligibility(eligibilityRes.data);
    } catch (error) {
      toast.error('Failed to load donor details');
      navigate('/donors');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  if (!donor) return null;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="donor-details">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/donors')} data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div className="flex-1">
          <h1 className="page-title">{donor.full_name}</h1>
          <p className="page-subtitle font-mono">{donor.donor_id}</p>
        </div>
        <Button
          onClick={() => navigate(`/screening?donor=${donor.id}`)}
          className="bg-teal-600 hover:bg-teal-700"
          disabled={!eligibility?.eligible}
          data-testid="start-screening-btn"
        >
          <Droplet className="w-4 h-4 mr-2" />
          Start Screening
        </Button>
      </div>

      {/* Eligibility Status */}
      <Card className={`border-l-4 ${eligibility?.eligible ? 'border-l-emerald-500' : 'border-l-red-500'}`}>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            {eligibility?.eligible ? (
              <>
                <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <p className="font-semibold text-emerald-700">Eligible to Donate</p>
                  <p className="text-sm text-slate-500">Donor can proceed with screening</p>
                </div>
              </>
            ) : (
              <>
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                  <XCircle className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <p className="font-semibold text-red-700">Not Eligible</p>
                  <ul className="text-sm text-slate-500 list-disc ml-4">
                    {eligibility?.issues?.map((issue, idx) => (
                      <li key={idx}>{issue}</li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-6">
          <Tabs defaultValue="info">
            <TabsList>
              <TabsTrigger value="info">Personal Info</TabsTrigger>
              <TabsTrigger value="donations">Donation History</TabsTrigger>
              <TabsTrigger value="screenings">Screening History</TabsTrigger>
            </TabsList>

            <TabsContent value="info" className="mt-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <p className="text-sm text-slate-500">Date of Birth</p>
                      <p className="font-medium">{donor.date_of_birth}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Gender</p>
                      <p className="font-medium">{donor.gender}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Blood Group</p>
                      {donor.blood_group ? (
                        <span className="blood-group-badge">{donor.blood_group}</span>
                      ) : (
                        <p className="text-slate-400">Not confirmed</p>
                      )}
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Phone</p>
                      <p className="font-medium">{donor.phone}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Email</p>
                      <p className="font-medium">{donor.email || '-'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Identity</p>
                      <p className="font-medium">{donor.identity_type}: {donor.identity_number}</p>
                    </div>
                    <div className="col-span-2">
                      <p className="text-sm text-slate-500">Address</p>
                      <p className="font-medium">{donor.address}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="donations" className="mt-4">
              <Card>
                <CardContent className="pt-6">
                  {history?.donations?.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      No donation history found
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Donation ID</TableHead>
                          <TableHead>Date</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Volume</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {history?.donations?.map((donation) => (
                          <TableRow key={donation.id}>
                            <TableCell className="font-mono">{donation.donation_id}</TableCell>
                            <TableCell>{donation.collection_start_time?.split('T')[0]}</TableCell>
                            <TableCell className="capitalize">{donation.donation_type?.replace('_', ' ')}</TableCell>
                            <TableCell>{donation.volume_collected || '-'} mL</TableCell>
                            <TableCell>
                              <Badge variant={donation.status === 'completed' ? 'default' : 'secondary'}>
                                {donation.status}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="screenings" className="mt-4">
              <Card>
                <CardContent className="pt-6">
                  {history?.screenings?.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      No screening history found
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Date</TableHead>
                          <TableHead>Hb (g/dL)</TableHead>
                          <TableHead>BP</TableHead>
                          <TableHead>Weight</TableHead>
                          <TableHead>Eligibility</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {history?.screenings?.map((screening) => (
                          <TableRow key={screening.id}>
                            <TableCell>{screening.screening_date}</TableCell>
                            <TableCell>{screening.hemoglobin}</TableCell>
                            <TableCell>{screening.blood_pressure_systolic}/{screening.blood_pressure_diastolic}</TableCell>
                            <TableCell>{screening.weight} kg</TableCell>
                            <TableCell>
                              <Badge variant={screening.eligibility_status === 'eligible' ? 'default' : 'destructive'}>
                                {screening.eligibility_status}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Side Panel */}
        <div className="space-y-6">
          {/* QR Code */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <QrCode className="w-4 h-4 text-teal-600" />
                Donor QR Code
              </CardTitle>
            </CardHeader>
            <CardContent className="flex justify-center">
              {donor.qr_code ? (
                <img 
                  src={`data:image/png;base64,${donor.qr_code}`} 
                  alt="Donor QR Code"
                  className="w-48 h-48 border rounded-lg"
                />
              ) : (
                <div className="w-48 h-48 bg-slate-100 rounded-lg flex items-center justify-center text-slate-400">
                  No QR Code
                </div>
              )}
            </CardContent>
          </Card>

          {/* Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <History className="w-4 h-4 text-teal-600" />
                Donation Stats
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Total Donations</span>
                <span className="font-bold text-2xl text-teal-600">{donor.total_donations || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Last Donation</span>
                <span className="font-medium">
                  {donor.last_donation_date 
                    ? new Date(donor.last_donation_date).toLocaleDateString() 
                    : 'Never'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Status</span>
                <Badge className={
                  donor.status === 'active' 
                    ? 'bg-emerald-100 text-emerald-700' 
                    : 'bg-red-100 text-red-700'
                }>
                  {donor.status?.replace('_', ' ')}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Deferral Info */}
          {donor.status !== 'active' && (
            <Card className="border-amber-200 bg-amber-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base text-amber-700">
                  <AlertTriangle className="w-4 h-4" />
                  Deferral Information
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <p><strong>Reason:</strong> {donor.deferral_reason || 'Not specified'}</p>
                {donor.deferral_end_date && (
                  <p><strong>Until:</strong> {donor.deferral_end_date}</p>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
