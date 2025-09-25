import Navigation from "@/components/Navigation";
import HeroSection from "@/components/HeroSection";
import FeaturedArtwork from "@/components/FeaturedArtwork";
import CommunityFeatures from "@/components/CommunityFeatures";

const Index = () => {
  return (
    <div className="min-h-screen">
      <Navigation />
      <HeroSection />
      <FeaturedArtwork />
      <CommunityFeatures />
    </div>
  );
};

export default Index;
