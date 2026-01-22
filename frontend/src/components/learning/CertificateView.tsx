'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Award,
  Download,
  Share2,
  CheckCircle,
  Star,
  Calendar,
  Clock,
  Trophy,
  Sparkles,
  ExternalLink,
  Copy,
  Check,
  X,
  Linkedin,
  Twitter
} from 'lucide-react';

// ==================== TYPES ====================

interface CertificateData {
  id: string;
  journey_title: string;
  journey_topic: string;
  user_name: string;
  issued_date: string;
  verification_code: string;
  total_xp_earned: number;
  stages_completed: number;
  packages_completed: number;
  exams_passed: number;
  total_study_hours: number;
  skills_acquired: string[];
  achievement_level: 'bronze' | 'silver' | 'gold' | 'platinum';
  theme_color: string;
}

interface CertificateViewProps {
  certificate: CertificateData;
  onClose: () => void;
}

// ==================== ACHIEVEMENT COLORS ====================

const ACHIEVEMENT_COLORS = {
  bronze: {
    bg: 'from-amber-600 to-amber-800',
    border: 'border-amber-500',
    text: 'text-amber-500',
    glow: 'shadow-amber-500/30'
  },
  silver: {
    bg: 'from-gray-400 to-gray-600',
    border: 'border-gray-400',
    text: 'text-gray-400',
    glow: 'shadow-gray-400/30'
  },
  gold: {
    bg: 'from-yellow-400 to-yellow-600',
    border: 'border-yellow-500',
    text: 'text-yellow-500',
    glow: 'shadow-yellow-500/30'
  },
  platinum: {
    bg: 'from-cyan-400 to-blue-500',
    border: 'border-cyan-400',
    text: 'text-cyan-400',
    glow: 'shadow-cyan-500/30'
  }
};

// ==================== CERTIFICATE VISUAL ====================

const CertificateVisual: React.FC<{ certificate: CertificateData }> = ({ certificate }) => {
  const colors = ACHIEVEMENT_COLORS[certificate.achievement_level];
  
  return (
    <div className="relative">
      {/* Glow Effect */}
      <div className={`absolute inset-0 bg-gradient-to-r ${colors.bg} blur-3xl opacity-30 -z-10`} />
      
      {/* Certificate Card */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', duration: 0.8 }}
        className={`relative bg-white dark:bg-gray-900 rounded-3xl border-4 ${colors.border} 
                   shadow-2xl ${colors.glow} overflow-hidden`}
      >
        {/* Decorative Corner Elements */}
        <div className="absolute top-0 left-0 w-24 h-24">
          <svg viewBox="0 0 100 100" className={colors.text}>
            <path
              d="M0 0 L100 0 L100 20 L20 20 L20 100 L0 100 Z"
              fill="currentColor"
              opacity="0.1"
            />
            <path
              d="M0 0 L60 0 L60 10 L10 10 L10 60 L0 60 Z"
              fill="currentColor"
              opacity="0.2"
            />
          </svg>
        </div>
        <div className="absolute bottom-0 right-0 w-24 h-24 rotate-180">
          <svg viewBox="0 0 100 100" className={colors.text}>
            <path
              d="M0 0 L100 0 L100 20 L20 20 L20 100 L0 100 Z"
              fill="currentColor"
              opacity="0.1"
            />
            <path
              d="M0 0 L60 0 L60 10 L10 10 L10 60 L0 60 Z"
              fill="currentColor"
              opacity="0.2"
            />
          </svg>
        </div>
        
        {/* Content */}
        <div className="p-8 md:p-12 text-center">
          {/* Header */}
          <div className="flex justify-center mb-6">
            <motion.div
              animate={{ rotate: [0, -10, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
              className={`p-4 rounded-full bg-gradient-to-br ${colors.bg}`}
            >
              <Award className="w-12 h-12 text-white" />
            </motion.div>
          </div>
          
          <h3 className="text-lg text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            Başarı Sertifikası
          </h3>
          
          <h2 className={`text-3xl md:text-4xl font-bold mt-2 bg-gradient-to-r ${colors.bg} bg-clip-text text-transparent`}>
            {certificate.achievement_level.toUpperCase()} SEVİYE
          </h2>
          
          {/* User Name */}
          <div className="mt-8">
            <p className="text-gray-500 dark:text-gray-400">Bu sertifika</p>
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mt-2 font-serif">
              {certificate.user_name}
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-2">adına düzenlenmiştir</p>
          </div>
          
          {/* Journey Info */}
          <div className="mt-8 py-6 border-y border-gray-200 dark:border-gray-700">
            <p className="text-gray-600 dark:text-gray-400">
              Aşağıdaki öğrenme yolculuğunu başarıyla tamamladığı için
            </p>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
              {certificate.journey_title}
            </h3>
            <p className={`mt-1 ${colors.text}`}>
              {certificate.journey_topic}
            </p>
          </div>
          
          {/* Stats */}
          <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: <Star className="w-5 h-5" />, value: certificate.total_xp_earned, label: 'XP' },
              { icon: <CheckCircle className="w-5 h-5" />, value: certificate.stages_completed, label: 'Aşama' },
              { icon: <Trophy className="w-5 h-5" />, value: certificate.exams_passed, label: 'Sınav' },
              { icon: <Clock className="w-5 h-5" />, value: `${certificate.total_study_hours}h`, label: 'Çalışma' },
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <div className={`inline-flex p-2 rounded-lg ${colors.text} bg-current/10 mb-1`}>
                  {stat.icon}
                </div>
                <div className="text-xl font-bold text-gray-900 dark:text-white">{stat.value}</div>
                <div className="text-xs text-gray-500">{stat.label}</div>
              </div>
            ))}
          </div>
          
          {/* Skills */}
          {certificate.skills_acquired.length > 0 && (
            <div className="mt-8">
              <p className="text-sm text-gray-500 mb-2">Edinilen Yetenekler</p>
              <div className="flex flex-wrap justify-center gap-2">
                {certificate.skills_acquired.map((skill, i) => (
                  <span
                    key={i}
                    className={`px-3 py-1 rounded-full text-sm ${colors.border} border bg-current/5 ${colors.text}`}
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-center gap-8 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {new Date(certificate.issued_date).toLocaleDateString('tr-TR', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </div>
              <div className="font-mono text-xs">
                #{certificate.verification_code}
              </div>
            </div>
          </div>
        </div>
        
        {/* Sparkle Effects */}
        {[...Array(5)].map((_, i) => (
          <motion.div
            key={i}
            className={`absolute ${colors.text}`}
            style={{
              top: `${20 + Math.random() * 60}%`,
              left: `${10 + Math.random() * 80}%`,
            }}
            animate={{
              scale: [0, 1, 0],
              opacity: [0, 1, 0],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              delay: i * 0.5,
            }}
          >
            <Sparkles className="w-4 h-4" />
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
};

// ==================== SHARE MODAL ====================

const ShareModal: React.FC<{
  certificate: CertificateData;
  onClose: () => void;
}> = ({ certificate, onClose }) => {
  const [copied, setCopied] = useState(false);
  const shareUrl = `${window.location.origin}/certificate/${certificate.id}`;
  
  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const shareText = `"${certificate.journey_title}" öğrenme yolculuğunu başarıyla tamamladım! 🎓`;
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-md w-full"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
            Sertifikayı Paylaş
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Social Share */}
        <div className="flex justify-center gap-4 mb-6">
          <a
            href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
          >
            <Linkedin className="w-6 h-6" />
          </a>
          <a
            href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 bg-sky-500 text-white rounded-xl hover:bg-sky-600 transition-colors"
          >
            <Twitter className="w-6 h-6" />
          </a>
        </div>
        
        {/* Copy Link */}
        <div className="relative">
          <input
            type="text"
            value={shareUrl}
            readOnly
            className="w-full p-3 pr-12 bg-gray-100 dark:bg-gray-700 rounded-xl text-sm"
          />
          <button
            onClick={handleCopy}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg"
          >
            {copied ? (
              <Check className="w-5 h-5 text-green-500" />
            ) : (
              <Copy className="w-5 h-5 text-gray-500" />
            )}
          </button>
        </div>
        
        {copied && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center text-green-500 text-sm mt-2"
          >
            Link kopyalandı!
          </motion.p>
        )}
      </motion.div>
    </motion.div>
  );
};

// ==================== MAIN CERTIFICATE VIEW ====================

const CertificateView: React.FC<CertificateViewProps> = ({ certificate, onClose }) => {
  const [showShareModal, setShowShareModal] = useState(false);
  const certificateRef = useRef<HTMLDivElement>(null);
  
  const handleDownload = async () => {
    // In real implementation, this would generate a PDF or image
    // For now, we'll show an alert
    try {
      const response = await fetch(`/api/journey/v2/certificate/${certificate.id}/download`);
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sertifika-${certificate.verification_code}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      alert('Sertifika indirme işlemi başarısız. Lütfen tekrar deneyin.');
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 p-4 md:p-8">
      {/* Header */}
      <div className="max-w-4xl mx-auto mb-6">
        <div className="flex items-center justify-between">
          <button
            onClick={onClose}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 
                       dark:hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
            Kapat
          </button>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowShareModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-xl 
                         hover:bg-blue-600 transition-colors"
            >
              <Share2 className="w-4 h-4" />
              Paylaş
            </button>
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-xl 
                         hover:bg-green-600 transition-colors"
            >
              <Download className="w-4 h-4" />
              İndir
            </button>
          </div>
        </div>
      </div>
      
      {/* Certificate */}
      <div className="max-w-4xl mx-auto" ref={certificateRef}>
        <CertificateVisual certificate={certificate} />
      </div>
      
      {/* Verification Info */}
      <div className="max-w-4xl mx-auto mt-8 text-center">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Bu sertifika <strong>{certificate.verification_code}</strong> kodu ile doğrulanabilir.
        </p>
        <a
          href={`/verify/${certificate.verification_code}`}
          className="inline-flex items-center gap-1 text-blue-500 hover:text-blue-600 text-sm mt-1"
        >
          Doğrula
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
      
      {/* Share Modal */}
      <AnimatePresence>
        {showShareModal && (
          <ShareModal
            certificate={certificate}
            onClose={() => setShowShareModal(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default CertificateView;
