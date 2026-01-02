import React, { useState, useEffect } from 'react';
import { rewardsAPI } from '../lib/api';
import { toast } from 'sonner';
import { 
  Trophy, Medal, Star, Award, Crown, TrendingUp, Users, 
  Droplet, RefreshCw, ChevronRight
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';

const TIER_COLORS = {
  bronze: 'bg-amber-600',
  silver: 'bg-slate-400',
  gold: 'bg-yellow-500',
  platinum: 'bg-cyan-400'
};

const TIER_BG_COLORS = {
  bronze: 'bg-amber-50 border-amber-200',
  silver: 'bg-slate-50 border-slate-200',
  gold: 'bg-yellow-50 border-yellow-200',
  platinum: 'bg-cyan-50 border-cyan-200'
};

const BADGE_ICONS = {
  first_donation: '🎉',
  donation_5: '⭐',
  donation_10: '🌟',
  donation_25: '💫',
  donation_50: '👑',
  rare_blood_type: '💎',
  emergency_donor: '🚨'
};

const BADGE_LABELS = {
  first_donation: 'First Donation',
  donation_5: '5 Donations',
  donation_10: '10 Donations',
  donation_25: '25 Donations',
  donation_50: '50 Donations',
  rare_blood_type: 'Rare Blood Type',
  emergency_donor: 'Emergency Donor'
};

export default function Leaderboard() {
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('all_time');
  const [leaderboard, setLeaderboard] = useState([]);
  const [totalDonors, setTotalDonors] = useState(0);

  useEffect(() => {
    fetchLeaderboard();
  }, [period]);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const response = await rewardsAPI.getLeaderboard(period, 100);
      setLeaderboard(response.data.leaderboard || []);
      setTotalDonors(response.data.total_donors || 0);
    } catch (error) {
      toast.error('Failed to fetch leaderboard');
    } finally {
      setLoading(false);
    }
  };

  const getTierIcon = (tier) => {
    switch (tier) {
      case 'platinum': return <Crown className="w-5 h-5 text-cyan-500" />;
      case 'gold': return <Trophy className="w-5 h-5 text-yellow-500" />;
      case 'silver': return <Medal className="w-5 h-5 text-slate-400" />;
      default: return <Award className="w-5 h-5 text-amber-600" />;
    }
  };

  const getRankBadge = (rank) => {
    if (rank === 1) return <div className="w-8 h-8 rounded-full bg-yellow-500 text-white flex items-center justify-center font-bold">1</div>;
    if (rank === 2) return <div className="w-8 h-8 rounded-full bg-slate-400 text-white flex items-center justify-center font-bold">2</div>;
    if (rank === 3) return <div className="w-8 h-8 rounded-full bg-amber-600 text-white flex items-center justify-center font-bold">3</div>;
    return <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center font-medium">{rank}</div>;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Trophy className="w-8 h-8 text-yellow-500" />
            Donor Leaderboard
          </h1>
          <p className="page-subtitle">Celebrating our blood donation heroes</p>
        </div>
        <Button variant="outline" onClick={fetchLeaderboard} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-yellow-600">Top Donors</p>
                <p className="text-2xl font-bold text-yellow-700">{totalDonors}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-yellow-200 flex items-center justify-center">
                <Users className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-cyan-50 to-cyan-100">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-cyan-600">Platinum Donors</p>
                <p className="text-2xl font-bold text-cyan-700">
                  {leaderboard.filter(d => d.tier === 'platinum').length}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-cyan-200 flex items-center justify-center">
                <Crown className="w-6 h-6 text-cyan-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-amber-50 to-amber-100">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-amber-600">Gold Donors</p>
                <p className="text-2xl font-bold text-amber-700">
                  {leaderboard.filter(d => d.tier === 'gold').length}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-amber-200 flex items-center justify-center">
                <Trophy className="w-6 h-6 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-red-50 to-red-100">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-600">Total Points Earned</p>
                <p className="text-2xl font-bold text-red-700">
                  {leaderboard.reduce((sum, d) => sum + d.points_earned, 0).toLocaleString()}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-red-200 flex items-center justify-center">
                <Star className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tier Legend */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Tier System</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full ${TIER_COLORS.platinum}`}></div>
              <span className="text-sm">Platinum (31+ donations)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full ${TIER_COLORS.gold}`}></div>
              <span className="text-sm">Gold (16-30 donations)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full ${TIER_COLORS.silver}`}></div>
              <span className="text-sm">Silver (6-15 donations)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full ${TIER_COLORS.bronze}`}></div>
              <span className="text-sm">Bronze (1-5 donations)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Leaderboard Tabs */}
      <Tabs value={period} onValueChange={setPeriod}>
        <TabsList>
          <TabsTrigger value="all_time">All Time</TabsTrigger>
          <TabsTrigger value="year">This Year</TabsTrigger>
          <TabsTrigger value="month">This Month</TabsTrigger>
        </TabsList>

        <TabsContent value={period} className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Donors</CardTitle>
              <CardDescription>
                {period === 'all_time' ? 'All time rankings' : 
                 period === 'year' ? 'Rankings for this year' : 'Rankings for this month'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
                </div>
              ) : leaderboard.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <Trophy className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  <p>No donors on the leaderboard yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-16">Rank</TableHead>
                      <TableHead>Donor</TableHead>
                      <TableHead>Blood Group</TableHead>
                      <TableHead className="text-center">Donations</TableHead>
                      <TableHead className="text-center">Points</TableHead>
                      <TableHead className="text-center">Tier</TableHead>
                      <TableHead className="text-center">Badges</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leaderboard.map((donor) => (
                      <TableRow key={donor.donor_id} className={donor.rank <= 3 ? 'bg-yellow-50/50' : ''}>
                        <TableCell>{getRankBadge(donor.rank)}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{donor.full_name}</p>
                            <p className="text-xs text-slate-500 font-mono">{donor.donor_id}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          {donor.blood_group ? (
                            <span className="blood-group-badge">{donor.blood_group}</span>
                          ) : '-'}
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="font-bold text-lg text-teal-600">{donor.total_donations}</span>
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="font-medium">{donor.points_earned.toLocaleString()}</span>
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-1">
                            {getTierIcon(donor.tier)}
                            <span className="capitalize text-sm">{donor.tier}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="outline">{donor.badges_count || 0}</Badge>
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

      {/* Points System Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-teal-600" />
            Points System
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium mb-2">Donation Points</h4>
              <ul className="space-y-1 text-sm text-slate-600">
                <li className="flex justify-between">
                  <span>Whole Blood</span>
                  <span className="font-medium text-teal-600">+10 pts</span>
                </li>
                <li className="flex justify-between">
                  <span>Apheresis (Platelets/Plasma)</span>
                  <span className="font-medium text-teal-600">+20 pts</span>
                </li>
                <li className="flex justify-between">
                  <span>Emergency Donation Bonus</span>
                  <span className="font-medium text-teal-600">+15 pts</span>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Milestone Bonuses</h4>
              <ul className="space-y-1 text-sm text-slate-600">
                <li className="flex justify-between">
                  <span>5 Donations</span>
                  <span className="font-medium text-teal-600">+50 pts</span>
                </li>
                <li className="flex justify-between">
                  <span>10 Donations</span>
                  <span className="font-medium text-teal-600">+100 pts</span>
                </li>
                <li className="flex justify-between">
                  <span>25 Donations</span>
                  <span className="font-medium text-teal-600">+250 pts</span>
                </li>
                <li className="flex justify-between">
                  <span>50 Donations</span>
                  <span className="font-medium text-teal-600">+500 pts</span>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Special Badges</h4>
              <div className="space-y-2">
                {Object.entries(BADGE_LABELS).slice(0, 5).map(([key, label]) => (
                  <div key={key} className="flex items-center gap-2 text-sm">
                    <span className="text-lg">{BADGE_ICONS[key]}</span>
                    <span>{label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
