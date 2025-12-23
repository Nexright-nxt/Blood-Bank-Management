import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { donorAPI } from '../lib/api';
import { toast } from 'sonner';
import { Plus, Search, Filter, Eye, UserCheck, UserX } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

const statusColors = {
  active: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  deferred_temporary: 'bg-amber-100 text-amber-700 border-amber-200',
  deferred_permanent: 'bg-red-100 text-red-700 border-red-200',
};

const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function DonorManagement() {
  const navigate = useNavigate();
  const [donors, setDonors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [bloodGroupFilter, setBloodGroupFilter] = useState('all');

  useEffect(() => {
    fetchDonors();
  }, [statusFilter, bloodGroupFilter]);

  const fetchDonors = async () => {
    try {
      const params = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (bloodGroupFilter !== 'all') params.blood_group = bloodGroupFilter;
      if (search) params.search = search;
      
      const response = await donorAPI.getAll(params);
      setDonors(response.data);
    } catch (error) {
      toast.error('Failed to fetch donors');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchDonors();
  };

  const filteredDonors = donors.filter(donor => {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    return (
      donor.full_name?.toLowerCase().includes(searchLower) ||
      donor.donor_id?.toLowerCase().includes(searchLower) ||
      donor.phone?.includes(search)
    );
  });

  return (
    <div className="space-y-6 animate-fade-in" data-testid="donor-management">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">Donor Management</h1>
          <p className="page-subtitle">Register and manage blood donors</p>
        </div>
        <Button 
          onClick={() => navigate('/donors/register')}
          className="bg-teal-600 hover:bg-teal-700"
          data-testid="register-donor-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Register New Donor
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search by name, ID, or phone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-9"
                data-testid="search-input"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-48" data-testid="status-filter">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="deferred_temporary">Temporarily Deferred</SelectItem>
                <SelectItem value="deferred_permanent">Permanently Deferred</SelectItem>
              </SelectContent>
            </Select>
            <Select value={bloodGroupFilter} onValueChange={setBloodGroupFilter}>
              <SelectTrigger className="w-full md:w-48" data-testid="blood-group-filter">
                <SelectValue placeholder="Filter by blood group" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Blood Groups</SelectItem>
                {bloodGroups.map(bg => (
                  <SelectItem key={bg} value={bg}>{bg}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={handleSearch} data-testid="search-btn">
              <Filter className="w-4 h-4 mr-2" />
              Apply
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Total Donors</p>
            <p className="text-2xl font-bold">{donors.length}</p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Active</p>
            <p className="text-2xl font-bold text-emerald-600">
              {donors.filter(d => d.status === 'active').length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Temp. Deferred</p>
            <p className="text-2xl font-bold text-amber-600">
              {donors.filter(d => d.status === 'deferred_temporary').length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Perm. Deferred</p>
            <p className="text-2xl font-bold text-red-600">
              {donors.filter(d => d.status === 'deferred_permanent').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Registered Donors</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
            </div>
          ) : filteredDonors.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              No donors found. Click "Register New Donor" to add one.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table className="table-dense">
                <TableHeader>
                  <TableRow>
                    <TableHead>Donor ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Blood Group</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Donations</TableHead>
                    <TableHead>Last Donation</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDonors.map((donor) => (
                    <TableRow key={donor.id} className="data-table-row" data-testid={`donor-row-${donor.id}`}>
                      <TableCell className="font-mono text-sm">{donor.donor_id}</TableCell>
                      <TableCell className="font-medium">{donor.full_name}</TableCell>
                      <TableCell>
                        {donor.blood_group ? (
                          <span className="blood-group-badge">{donor.blood_group}</span>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>{donor.phone}</TableCell>
                      <TableCell>
                        <Badge className={`${statusColors[donor.status]} border`}>
                          {donor.status === 'active' ? (
                            <><UserCheck className="w-3 h-3 mr-1" /> Active</>
                          ) : donor.status === 'deferred_temporary' ? (
                            <><UserX className="w-3 h-3 mr-1" /> Temp. Deferred</>
                          ) : (
                            <><UserX className="w-3 h-3 mr-1" /> Perm. Deferred</>
                          )}
                        </Badge>
                      </TableCell>
                      <TableCell>{donor.total_donations || 0}</TableCell>
                      <TableCell>
                        {donor.last_donation_date ? (
                          new Date(donor.last_donation_date).toLocaleDateString()
                        ) : (
                          <span className="text-slate-400">Never</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/donors/${donor.id}`)}
                          data-testid={`view-donor-${donor.id}`}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
