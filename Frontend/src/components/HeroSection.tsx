import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles } from "lucide-react";

const HeroSection = () => {
  return (
    <section className="relative overflow-hidden bg-gradient-hero min-h-[80vh] flex items-center">
      {/* Decorative elements */}
      <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent"></div>
      <div className="absolute top-20 left-10 w-32 h-32 bg-white/10 rounded-full blur-xl"></div>
      <div className="absolute bottom-20 right-10 w-48 h-48 bg-white/5 rounded-full blur-2xl"></div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center space-x-2 bg-white/20 backdrop-blur-sm rounded-full px-4 py-2 mb-6">
            <Sparkles className="h-4 w-4 text-yellow-bright" />
            <span className="text-sm font-medium">Join the Art Revolution</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/80">
            Create. Connect. 
            <br />
            <span className="text-white">Collaborate.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-white/90 mb-8 max-w-2xl mx-auto leading-relaxed">
            Connect with young artists worldwide. Discover incredible artwork, showcase your creativity, 
            and join a vibrant community of creators pushing the boundaries of digital art.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4">
            <Button variant="hero" size="lg" className="group">
              Start Creating
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
            <Button variant="hero-outline" size="lg">
              Explore Talent
            </Button>
          </div>
          
          <div className="mt-12 flex items-center justify-center space-x-8 text-white/70">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">10K+</div>
              <div className="text-sm">Artists</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">50K+</div>
              <div className="text-sm">Artworks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">25K+</div>
              <div className="text-sm">Collaborations</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;