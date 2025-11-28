import { useNavigate } from 'react-router-dom';

export const CampaignSelectorRoute = () => {
  const navigate = useNavigate();
  
  // Mock campaigns
  const campaigns = [
    { id: '1', name: 'Curse of Strahd', role: 'DM', image: 'https://images.unsplash.com/photo-1599058945522-28d584b6f0ff?q=80&w=2669&auto=format&fit=crop' },
    { id: '2', name: 'Lost Mine of Phandelver', role: 'Player', image: 'https://images.unsplash.com/photo-1519074069444-1ba4fff66d16?q=80&w=2574&auto=format&fit=crop' },
  ];

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-heading text-primary mb-8">Select Campaign</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {campaigns.map(c => (
            <div 
              key={c.id}
              onClick={() => navigate(`/session/${c.id}`)}
              className="group relative aspect-video bg-card border border-border rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary transition-all"
            >
              <img src={c.image} alt={c.name} className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/90 to-transparent" />
              
              <div className="absolute bottom-0 left-0 p-4">
                <h3 className="text-xl font-bold text-white">{c.name}</h3>
                <span className="text-xs uppercase tracking-wider text-primary font-medium">{c.role}</span>
              </div>
            </div>
          ))}
          
          {/* Create New */}
          <div className="aspect-video bg-muted/20 border-2 border-dashed border-muted rounded-lg flex flex-col items-center justify-center cursor-pointer hover:bg-muted/30 transition-colors">
            <span className="text-4xl mb-2 text-muted-foreground">+</span>
            <span className="text-muted-foreground font-medium">Create New</span>
          </div>
        </div>
      </div>
    </div>
  );
};
