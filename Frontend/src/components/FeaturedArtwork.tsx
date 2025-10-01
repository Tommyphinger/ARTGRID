import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Heart, Share2, Eye } from "lucide-react";
import featuredArtwork1 from "@/assets/featured-artwork-1.jpg";
import featuredArtwork2 from "@/assets/featured-artwork-2.jpg";
import featuredArtwork3 from "@/assets/featured-artwork-3.jpg";

const artworks = [
  {
    id: 1,
    title: "Digital Portrait: Emma",
    artist: "Sarah Johnson",
    category: "Digital Art",
    image: featuredArtwork1,
    likes: 245,
    views: 1200,
  },
  {
    id: 2,
    title: "Abstract Composition #4",
    artist: "Marcus Chen",
    category: "Abstract",
    image: featuredArtwork2,
    likes: 189,
    views: 890,
  },
  {
    id: 3,
    title: "Urban Landscape",
    artist: "Elena Rodriguez",
    category: "Photography",
    image: featuredArtwork3,
    likes: 312,
    views: 1540,
  },
  {
    id: 4,
    title: "Color Study in Motion",
    artist: "David Kim",
    category: "Digital Art",
    image: featuredArtwork1,
    likes: 167,
    views: 720,
  },
  {
    id: 5,
    title: "Geometric Dreams",
    artist: "Luna Martinez",
    category: "Abstract",
    image: featuredArtwork2,
    likes: 203,
    views: 980,
  },
  {
    id: 6,
    title: "Street Reflections",
    artist: "Alex Thompson",
    category: "Photography",
    image: featuredArtwork3,
    likes: 278,
    views: 1350,
  },
];

const FeaturedArtwork = () => {
  return (
    <section className="py-20 bg-background">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Discover Amazing <span className="text-coral">Artwork</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Explore the latest creations from our talented community of artists
          </p>
          
          <div className="flex items-center justify-center space-x-4 mt-8">
            <Button variant="teal" size="sm">Latest</Button>
            <Button variant="ghost" size="sm">Trending</Button>
            <Button variant="ghost" size="sm">Following</Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {artworks.map((artwork) => (
            <Card key={artwork.id} className="group overflow-hidden hover:shadow-elegant transition-all duration-300 hover:-translate-y-1">
              <div className="relative overflow-hidden">
                <img
                  src={artwork.image}
                  alt={artwork.title}
                  className="w-full h-64 object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div className="flex space-x-2">
                    <Button size="sm" variant="ghost" className="bg-white/20 backdrop-blur-sm text-white hover:bg-white/30" aria-label="Like">
                      <Heart className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="ghost" className="bg-white/20 backdrop-blur-sm text-white hover:bg-white/30" aria-label="Share">
                      <Share2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
              
              <div className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-coral bg-coral/10 px-2 py-1 rounded-full">
                    {artwork.category}
                  </span>
                  <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                    <div className="flex items-center space-x-1">
                      <Heart className="h-3 w-3" />
                      <span>{artwork.likes}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Eye className="h-3 w-3" />
                      <span>{artwork.views}</span>
                    </div>
                  </div>
                </div>
                
                <h3 className="font-semibold text-lg mb-1 group-hover:text-coral transition-colors">
                  {artwork.title}
                </h3>
                <p className="text-sm text-muted-foreground">by {artwork.artist}</p>
              </div>
            </Card>
          ))}
        </div>

        <div className="text-center">
          <Button variant="accent" size="lg">
            View All Artwork
          </Button>
        </div>
      </div>
    </section>
  );
};

export default FeaturedArtwork;