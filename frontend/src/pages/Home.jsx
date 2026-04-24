import { Link } from 'react-router-dom'
import {
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  HeartIcon,
  SparklesIcon,
  MagnifyingGlassCircleIcon,
  ShieldCheckIcon,
  LockClosedIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline'

export default function Home() {
  const usps = [
    {
      title: 'AI Assistant',
      desc: 'Answers are grounded in your data and trusted medical sources, with clear safety language.',
      icon: ChatBubbleLeftRightIcon,
    },
    {
      title: 'Report Parsing',
      desc: 'Upload clinical PDFs and convert complex oncology terms into understandable summaries.',
      icon: DocumentTextIcon,
    },
    {
      title: 'Nutrition Planner',
      desc: 'Generate personalized meal guidance aligned to treatment stage, symptoms, and tolerances.',
      icon: SparklesIcon,
    },
    {
      title: 'Symptom Tracking',
      desc: 'Log symptoms over time and surface trends that help with more informed consultations.',
      icon: HeartIcon,
    },
    {
      title: 'Trial Discovery',
      desc: 'Search active studies by cancer type and review key trial details quickly.',
      icon: MagnifyingGlassCircleIcon,
    },
  ]

  return (
    <div className="min-h-screen bg-[#f4f7fb] flex flex-col text-slate-800 selection:bg-teal-100 selection:text-teal-900 overflow-x-hidden">
      <nav className="sticky top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-6 md:px-10 py-4 flex justify-between items-center">
          <span className="font-extrabold text-xl tracking-tight brand-text">CancerCare</span>
          <div className="flex gap-4 items-center">
            <Link to="/login" className="text-sm font-semibold text-slate-600 hover:text-teal-700 transition-colors hidden sm:block">
              Log In
            </Link>
            <Link to="/login" className="btn-primary text-sm px-5 py-2.5">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      <section className="pt-16 md:pt-20 pb-12 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
          <div className="animate-slide-up">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-100 text-teal-800 text-xs font-semibold mb-6">
              Clinical Decision Support Companion
            </div>
            <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 leading-tight tracking-tight">
              A safer, clearer way to manage your cancer care journey.
            </h1>
            <p className="text-slate-600 mt-5 text-lg max-w-xl leading-relaxed">
              CancerCare AI helps patients and caregivers track symptoms, understand reports, and prepare for better conversations with clinicians.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 mt-8">
              <Link to="/login" className="btn-primary px-6 py-3 text-sm text-center">
                Create Account
              </Link>
              <a href="#features" className="btn-secondary px-6 py-3 text-sm text-center">
                Explore Features
              </a>
            </div>
          </div>

          <div className="surface-card p-6 md:p-8 animate-fade-in">
            <h2 className="text-sm font-semibold text-slate-700 mb-4">Why patients trust CancerCare AI</h2>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <ShieldCheckIcon className="h-5 w-5 text-teal-700 mt-0.5" />
                <p className="text-sm text-slate-600">Grounded response style with clear medical disclaimers and non-diagnostic language.</p>
              </div>
              <div className="flex items-start gap-3">
                <LockClosedIcon className="h-5 w-5 text-teal-700 mt-0.5" />
                <p className="text-sm text-slate-600">Secure account-based access with separate patient and caregiver workflows.</p>
              </div>
              <div className="flex items-start gap-3">
                <UserGroupIcon className="h-5 w-5 text-teal-700 mt-0.5" />
                <p className="text-sm text-slate-600">Shared visibility across care circles through caregiver linking and portal summaries.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="py-14 md:py-20 bg-white border-y border-slate-100">
        <div className="max-w-7xl mx-auto px-6">
          <div className="max-w-2xl mb-10">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">Core capabilities for everyday oncology care</h2>
            <p className="text-slate-600">Each workflow is designed to reduce friction, improve clarity, and support safer communication with your care team.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {usps.map((usp, index) => (
              <div key={index} className="surface-card surface-card-hover p-6">
                <div className="w-11 h-11 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center mb-4 border border-teal-100">
                  <usp.icon className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{usp.title}</h3>
                <p className="text-slate-600 text-sm leading-relaxed">{usp.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="py-12 bg-[#f4f7fb] text-center">
        <div className="max-w-7xl mx-auto px-6">
          <div className="mb-6">
            <span className="font-bold text-slate-900">CancerCare</span>
          </div>
          <p className="text-slate-500 text-sm max-w-2xl mx-auto leading-relaxed">
            Educational support tool only. CancerCare AI does not provide medical diagnosis or treatment advice.
            Always follow guidance from licensed oncology professionals.
          </p>
          <div className="mt-8 pt-6 border-t border-slate-200 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-slate-500">© 2026 CancerCare Global. All rights reserved.</p>
            <div className="flex gap-6">
              <a href="#" className="text-xs font-semibold text-slate-500 hover:text-teal-700">Privacy</a>
              <a href="#" className="text-xs font-semibold text-slate-500 hover:text-teal-700">Clinical Data</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

