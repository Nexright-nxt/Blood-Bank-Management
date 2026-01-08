import React, { useState, useEffect } from 'react';
import { Lock, Mail, KeyRound, Shield, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { sensitiveActionsAPI } from '../lib/api';
import { toast } from 'sonner';

/**
 * SensitiveActionModal - Re-authentication modal for sensitive admin actions
 * 
 * Usage:
 * <SensitiveActionModal
 *   open={showModal}
 *   onOpenChange={setShowModal}
 *   actionType="delete_user"
 *   actionTitle="Delete User"
 *   actionDescription="You are about to delete a user account. This action cannot be undone."
 *   targetId={userId}
 *   onVerified={(token) => handleDelete(token)}
 * />
 */

export default function SensitiveActionModal({
  open,
  onOpenChange,
  actionType,
  actionTitle = "Confirm Action",
  actionDescription = "Please verify your identity to proceed with this action.",
  targetId = null,
  onVerified,
  onCancel
}) {
  const [verificationMethod, setVerificationMethod] = useState('password');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [verificationId, setVerificationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpEmail, setOtpEmail] = useState('');
  const [error, setError] = useState('');
  const [demoOtp, setDemoOtp] = useState(''); // For development only

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!open) {
      setPassword('');
      setOtp('');
      setVerificationId(null);
      setOtpSent(false);
      setError('');
      setDemoOtp('');
      setVerificationMethod('password');
    }
  }, [open]);

  const handlePasswordVerify = async () => {
    if (!password.trim()) {
      setError('Please enter your password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await sensitiveActionsAPI.verifyPassword({
        password,
        action_type: actionType,
        target_id: targetId
      });

      if (response.data.verified) {
        toast.success('Verification successful');
        onVerified(response.data.verification_token);
        onOpenChange(false);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestOtp = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await sensitiveActionsAPI.requestOtp({
        action_type: actionType,
        target_id: targetId
      });

      setVerificationId(response.data.verification_id);
      setOtpEmail(response.data.message);
      setOtpSent(true);
      
      // For demo/development - show OTP in toast
      if (response.data.demo_otp) {
        setDemoOtp(response.data.demo_otp);
        toast.info(`Demo OTP: ${response.data.demo_otp}`, { duration: 10000 });
      }
      
      toast.success('OTP sent to your email');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpVerify = async () => {
    if (!otp.trim() || otp.length !== 6) {
      setError('Please enter the 6-digit OTP');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await sensitiveActionsAPI.verifyOtp({
        otp,
        verification_id: verificationId,
        action_type: actionType,
        target_id: targetId
      });

      if (response.data.verified) {
        toast.success('Verification successful');
        onVerified(response.data.verification_token);
        onOpenChange(false);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (onCancel) onCancel();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-amber-500" />
            {actionTitle}
          </DialogTitle>
          <DialogDescription>
            {actionDescription}
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <Alert className="mb-4 bg-amber-50 border-amber-200">
            <AlertCircle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-800">
              For security, please verify your identity to continue.
            </AlertDescription>
          </Alert>

          <Tabs value={verificationMethod} onValueChange={setVerificationMethod}>
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="password" className="gap-2">
                <Lock className="w-4 h-4" />
                Password
              </TabsTrigger>
              <TabsTrigger value="otp" className="gap-2">
                <Mail className="w-4 h-4" />
                Email OTP
              </TabsTrigger>
            </TabsList>

            {/* Password Verification */}
            <TabsContent value="password" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="password">Enter your password</Label>
                <div className="relative">
                  <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10"
                    onKeyDown={(e) => e.key === 'Enter' && handlePasswordVerify()}
                    disabled={loading}
                  />
                </div>
              </div>

              {error && (
                <Alert variant="destructive" className="py-2">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button 
                onClick={handlePasswordVerify} 
                className="w-full"
                disabled={loading || !password}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Verify & Continue
                  </>
                )}
              </Button>
            </TabsContent>

            {/* Email OTP Verification */}
            <TabsContent value="otp" className="space-y-4">
              {!otpSent ? (
                <>
                  <p className="text-sm text-slate-600">
                    We'll send a verification code to your registered email address.
                  </p>
                  
                  {error && (
                    <Alert variant="destructive" className="py-2">
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}

                  <Button 
                    onClick={handleRequestOtp} 
                    className="w-full"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Sending OTP...
                      </>
                    ) : (
                      <>
                        <Mail className="w-4 h-4 mr-2" />
                        Send OTP to Email
                      </>
                    )}
                  </Button>
                </>
              ) : (
                <>
                  <Alert className="bg-emerald-50 border-emerald-200">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <AlertDescription className="text-emerald-800">
                      {otpEmail}
                    </AlertDescription>
                  </Alert>

                  {demoOtp && (
                    <Alert className="bg-blue-50 border-blue-200">
                      <AlertDescription className="text-blue-800 font-mono">
                        Demo OTP: <strong>{demoOtp}</strong>
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="otp">Enter 6-digit OTP</Label>
                    <Input
                      id="otp"
                      type="text"
                      placeholder="000000"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      className="text-center text-2xl tracking-widest font-mono"
                      maxLength={6}
                      onKeyDown={(e) => e.key === 'Enter' && handleOtpVerify()}
                      disabled={loading}
                    />
                  </div>

                  {error && (
                    <Alert variant="destructive" className="py-2">
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}

                  <div className="flex gap-2">
                    <Button 
                      variant="outline"
                      onClick={handleRequestOtp}
                      disabled={loading}
                      className="flex-1"
                    >
                      Resend OTP
                    </Button>
                    <Button 
                      onClick={handleOtpVerify}
                      disabled={loading || otp.length !== 6}
                      className="flex-1"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Verifying...
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-4 h-4 mr-2" />
                          Verify
                        </>
                      )}
                    </Button>
                  </div>
                </>
              )}
            </TabsContent>
          </Tabs>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={handleCancel} disabled={loading}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
