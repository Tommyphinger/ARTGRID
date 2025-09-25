import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Users, Palette, Trophy, MessageCircle } from "lucide-react";

const features = [
  {
    icon: Palette,
    title: "Create Without Limits",
    description: "Access professional digital art tools and unlimited cloud storage for your creative projects.",
    color: "coral",
  },
  {
    icon: Users,
    title: "Connect & Collaborate",
    description: "Find artists with complementary skills and work together on amazing collaborative projects.",
    color: "teal",
  },
  {
    icon: Trophy,
    title: "Showcase Your Work",
    description: "Build your portfolio, get discovered by art collectors, and participate in community challenges.",
    color: "mint",
  },
  {
    icon: MessageCircle,
    title: "Learn & Grow",
    description: "Join workshops, get feedback from experienced artists, and level up your creative skills.",
    color: "yellow-bright",
  },
];

const CommunityFeatures = () => {
  return (
    <section className="py-20 bg-mint/10">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Why Join <span className="text-teal">ArtGrid</span>?
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Everything you need to grow as an artist and connect with a global creative community
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card key={index} className="text-center p-8 hover:shadow-elegant transition-all duration-300 hover:-translate-y-2 border-0 bg-white/80 backdrop-blur-sm">
                <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full bg-${feature.color}/20 mb-6`}>
                  <Icon className={`h-8 w-8 text-${feature.color}`} />
                </div>
                <h3 className="text-xl font-semibold mb-4">{feature.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed mb-6">
                  {feature.description}
                </p>
                <Button variant="ghost" size="sm" className="text-coral hover:text-coral hover:bg-coral/10">
                  Learn More →
                </Button>
              </Card>
            );
          })}
        </div>

        <div className="text-center mt-16">
          <div className="bg-gradient-card rounded-2xl p-8 md:p-12 text-white">
            <h3 className="text-2xl md:text-3xl font-bold mb-4">
              Ready to Join the Revolution?
            </h3>
            <p className="text-lg opacity-90 mb-8 max-w-xl mx-auto">
              Join thousands of artists already creating, connecting, and collaborating on ArtGrid
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4">
              <Button variant="hero" size="lg">
                Get Started Free
              </Button>
              <Button variant="hero-outline" size="lg" className="border-white text-white hover:bg-white hover:text-teal">
                View Pricing
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CommunityFeatures;