import React, { useState, useEffect, useRef } from 'react';
import { Html5QrcodeScanner, Html5Qrcode } from 'html5-qrcode';
import { ScanLine, X, Camera, CameraOff, Zap, Package, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import { toast } from 'sonner';

export default function BarcodeScanner({ 
  open, 
  onOpenChange, 
  onScan,
  bulkMode = false,
  title = 'Scan Barcode'
}) {
  const [scanning, setScanning] = useState(false);
  const [lastScanned, setLastScanned] = useState(null);
  const [scannedItems, setScannedItems] = useState([]);
  const [error, setError] = useState(null);
  const scannerRef = useRef(null);
  const html5QrcodeRef = useRef(null);

  useEffect(() => {
    if (open && !scanning) {
      startScanner();
    }
    
    return () => {
      stopScanner();
    };
  }, [open]);

  const startScanner = async () => {
    setError(null);
    setScanning(true);
    
    try {
      // Create scanner instance
      const html5Qrcode = new Html5Qrcode("barcode-reader");
      html5QrcodeRef.current = html5Qrcode;
      
      const config = {
        fps: 10,
        qrbox: { width: 300, height: 150 },
        aspectRatio: 2.0,
        formatsToSupport: [
          0, // QR_CODE
          1, // AZTEC
          2, // CODABAR
          3, // CODE_39
          4, // CODE_93
          5, // CODE_128
          6, // DATA_MATRIX
          7, // MAXICODE
          8, // ITF
          9, // EAN_13
          10, // EAN_8
          11, // PDF_417
          12, // RSS_14
          13, // RSS_EXPANDED
          14, // UPC_A
          15, // UPC_E
          16, // UPC_EAN_EXTENSION
        ],
      };
      
      await html5Qrcode.start(
        { facingMode: "environment" },
        config,
        onScanSuccess,
        onScanFailure
      );
    } catch (err) {
      console.error("Scanner error:", err);
      setError(err.message || "Failed to start camera. Please ensure camera permissions are granted.");
      setScanning(false);
    }
  };

  const stopScanner = async () => {
    if (html5QrcodeRef.current) {
      try {
        await html5QrcodeRef.current.stop();
        html5QrcodeRef.current = null;
      } catch (err) {
        console.error("Error stopping scanner:", err);
      }
    }
    setScanning(false);
  };

  const onScanSuccess = (decodedText, decodedResult) => {
    // Vibrate if supported
    if (navigator.vibrate) {
      navigator.vibrate(100);
    }
    
    // Play beep sound
    playBeep();
    
    setLastScanned(decodedText);
    
    if (bulkMode) {
      // Add to scanned items list (avoid duplicates)
      setScannedItems(prev => {
        if (prev.includes(decodedText)) {
          toast.info('Item already scanned');
          return prev;
        }
        toast.success(`Scanned: ${decodedText}`);
        return [...prev, decodedText];
      });
    } else {
      // Single scan mode - close and return result
      toast.success(`Scanned: ${decodedText}`);
      stopScanner();
      if (onScan) {
        onScan(decodedText);
      }
      onOpenChange(false);
    }
  };

  const onScanFailure = (errorMessage) => {
    // Silent fail - this fires continuously when no barcode is detected
  };

  const playBeep = () => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = 1000;
      oscillator.type = 'sine';
      gainNode.gain.value = 0.3;
      
      oscillator.start();
      setTimeout(() => {
        oscillator.stop();
        audioContext.close();
      }, 100);
    } catch (e) {
      // Audio not supported
    }
  };

  const handleFinishBulkScan = () => {
    stopScanner();
    if (onScan && scannedItems.length > 0) {
      onScan(scannedItems);
    }
    onOpenChange(false);
    setScannedItems([]);
  };

  const removeScannedItem = (item) => {
    setScannedItems(prev => prev.filter(i => i !== item));
  };

  const handleClose = () => {
    stopScanner();
    setScannedItems([]);
    setLastScanned(null);
    setError(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ScanLine className="w-5 h-5 text-teal-600" />
            {title}
          </DialogTitle>
          <DialogDescription>
            {bulkMode 
              ? 'Scan multiple barcodes. Items will be added to the list below.'
              : 'Position the barcode within the scanning area.'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Scanner View */}
          <div className="relative">
            <div 
              id="barcode-reader" 
              ref={scannerRef}
              className="w-full rounded-lg overflow-hidden bg-black"
              style={{ minHeight: '250px' }}
            />
            
            {/* Scanning indicator */}
            {scanning && !error && (
              <div className="absolute top-2 right-2">
                <Badge className="bg-emerald-500 animate-pulse">
                  <Camera className="w-3 h-3 mr-1" />
                  Scanning...
                </Badge>
              </div>
            )}
            
            {/* Error message */}
            {error && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/80 rounded-lg">
                <div className="text-center p-4">
                  <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-2" />
                  <p className="text-white text-sm">{error}</p>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="mt-3"
                    onClick={startScanner}
                  >
                    Retry
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Last Scanned */}
          {lastScanned && !bulkMode && (
            <Card className="p-3 bg-emerald-50 border-emerald-200">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-emerald-600" />
                <span className="text-sm text-emerald-700">Last scanned:</span>
                <span className="font-mono font-bold text-emerald-800">{lastScanned}</span>
              </div>
            </Card>
          )}

          {/* Bulk Mode: Scanned Items List */}
          {bulkMode && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">
                  Scanned Items ({scannedItems.length})
                </span>
                {scannedItems.length > 0 && (
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => setScannedItems([])}
                  >
                    Clear All
                  </Button>
                )}
              </div>
              
              <div className="max-h-40 overflow-y-auto space-y-1 border rounded-lg p-2">
                {scannedItems.length === 0 ? (
                  <div className="text-center py-4 text-slate-400 text-sm">
                    No items scanned yet
                  </div>
                ) : (
                  scannedItems.map((item, idx) => (
                    <div 
                      key={idx}
                      className="flex items-center justify-between bg-slate-50 rounded px-2 py-1"
                    >
                      <div className="flex items-center gap-2">
                        <Package className="w-4 h-4 text-slate-400" />
                        <span className="font-mono text-sm">{item}</span>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => removeScannedItem(item)}
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2 border-t">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            {bulkMode && (
              <Button 
                onClick={handleFinishBulkScan}
                disabled={scannedItems.length === 0}
                className="bg-teal-600 hover:bg-teal-700"
              >
                Done ({scannedItems.length} items)
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Simple scanner button component
export function ScanButton({ onScan, bulkMode = false, className = '' }) {
  const [showScanner, setShowScanner] = useState(false);
  
  return (
    <>
      <Button 
        variant="outline" 
        onClick={() => setShowScanner(true)}
        className={className}
      >
        <ScanLine className="w-4 h-4 mr-1" />
        {bulkMode ? 'Bulk Scan' : 'Scan'}
      </Button>
      
      <BarcodeScanner 
        open={showScanner}
        onOpenChange={setShowScanner}
        onScan={onScan}
        bulkMode={bulkMode}
        title={bulkMode ? 'Bulk Barcode Scan' : 'Scan Barcode'}
      />
    </>
  );
}
