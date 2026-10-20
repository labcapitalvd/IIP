import React from 'react';
import {
  Building2, Sparkles, Cpu, Rocket, Layers, Users, Lightbulb, Target, Scale, Landmark,
  BarChart3, ShieldCheck, Network, BookOpen, Handshake, Leaf, Globe, Wallet,
} from 'lucide-react';

export const FORM_ICONS: Record<string, { label: string; Icon: React.ElementType }> = {
  Building2: { label: 'Institución', Icon: Building2 },
  Sparkles: { label: 'Cultura', Icon: Sparkles },
  Cpu: { label: 'Tecnología', Icon: Cpu },
  Rocket: { label: 'Proyectos', Icon: Rocket },
  Layers: { label: 'Estrategia', Icon: Layers },
  Users: { label: 'Talento humano', Icon: Users },
  Lightbulb: { label: 'Ideas', Icon: Lightbulb },
  Target: { label: 'Objetivos', Icon: Target },
  Scale: { label: 'Normatividad', Icon: Scale },
  Landmark: { label: 'Gobierno', Icon: Landmark },
  BarChart3: { label: 'Medición', Icon: BarChart3 },
  ShieldCheck: { label: 'Control', Icon: ShieldCheck },
  Network: { label: 'Articulación', Icon: Network },
  BookOpen: { label: 'Conocimiento', Icon: BookOpen },
  Handshake: { label: 'Alianzas', Icon: Handshake },
  Leaf: { label: 'Sostenibilidad', Icon: Leaf },
  Globe: { label: 'Ciudadanía', Icon: Globe },
  Wallet: { label: 'Presupuesto', Icon: Wallet },
};

export const FormIcon: React.FC<{ name?: string; className?: string }> = ({ name, className }) => {
  const Icon = (name && FORM_ICONS[name]?.Icon) || Layers;
  return <Icon className={className || 'w-4 h-4'} />;
};
