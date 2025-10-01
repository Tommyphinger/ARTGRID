import { Button } from "@/components/ui/button";
import artgridLogo from "@/assets/artgrid-logo.png";
import { Search, Menu } from "lucide-react";

const Navigation = () => {
  return (
    <nav className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-2">
            <img 
              src={artgridLogo} 
              alt="ArtGrid" 
              className="h-8 w-8 object-contain"
            />
            <span className="text-xl font-bold">ARTGRID</span>
          </div>
          
          <div className="hidden md:flex items-center space-x-6">
            <a href="#" className="text-sm font-medium hover:text-coral transition-colors">
              Home
            </a>
            <a href="#" className="text-sm font-medium hover:text-coral transition-colors">
              Gallery
            </a>
            <a href="#" className="text-sm font-medium hover:text-coral transition-colors">
              Create
            </a>
            <a href="#" className="text-sm font-medium hover:text-coral transition-colors">
              Community
            </a>
            <a href="#" className="text-sm font-medium hover:text-coral transition-colors">
              About
            </a>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center">
            <Search className="h-4 w-4 text-muted-foreground" />
          </div>
          <Button variant="hero" size="sm">
            Sign Up
          </Button>
          <Button variant="ghost" size="sm" className="md:hidden" aria-label="Open menu">
            <Menu className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;