'use client';

import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

// Types based on Django models
interface Course {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  duration: string;
  monthly_fee: number;
}

const fetchCourses = async (): Promise<Course[]> => {
  const { data } = await apiClient.get('/academics/courses/');
  return data;
};

export default function Home() {
  const { data: courses, isLoading } = useQuery({
    queryKey: ['courses'],
    queryFn: fetchCourses,
  });

  return (
    <main className="min-h-screen flex flex-col items-center">
      {/* Hero Section */}
      <section className="relative w-full py-32 lg:py-48 flex flex-col items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-background/50 z-10" />
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1542838686-37ed7a928b04?q=80&w=2000&auto=format&fit=crop')] bg-cover bg-center opacity-30" />
        
        <div className="container relative z-20 flex flex-col items-center text-center space-y-8 px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-sm font-medium text-primary backdrop-blur-sm"
          >
            Admissions Open for 2024
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-5xl md:text-7xl font-bold tracking-tight max-w-4xl"
          >
            The Divine Art of <br />
            <span className="text-gradient">Kuchipudi</span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-lg md:text-xl text-muted-foreground max-w-2xl"
          >
            Welcome to Perin Devi Natyalayam. Immerse yourself in the rich heritage, intricate footwork, and expressive storytelling of India&apos;s classical dance.
          </motion.p>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="flex gap-4 pt-4"
          >
            <Button size="lg" className="h-12 px-8 text-base font-semibold shadow-[0_0_20px_rgba(242,192,41,0.3)]">
              Explore Courses
            </Button>
            <Button size="lg" variant="outline" className="h-12 px-8 text-base border-primary/50 hover:bg-primary/10">
              Our Heritage
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Courses Section */}
      <section className="w-full py-24 bg-card/30">
        <div className="container px-4 mx-auto">
          <div className="flex flex-col items-center mb-16 space-y-4">
            <h2 className="text-3xl md:text-5xl font-bold">Featured Courses</h2>
            <div className="h-1 w-24 bg-primary rounded-full" />
            <p className="text-muted-foreground text-center max-w-2xl">
              From beginners taking their first steps to advanced performers perfecting their expressions, we have a curriculum for everyone.
            </p>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[1, 2, 3].map((i) => (
                <div key={i} className="glass-card h-80 rounded-2xl animate-pulse bg-muted/20" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {courses?.length === 0 ? (
                <div className="col-span-full text-center text-muted-foreground py-12">
                  No courses available at the moment.
                </div>
              ) : (
                courses?.map((course, i) => (
                  <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: i * 0.1 }}
                    key={course.id} 
                    className="glass-card p-8 rounded-2xl flex flex-col group"
                  >
                    <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center mb-6 text-primary group-hover:scale-110 transition-transform">
                      ✦
                    </div>
                    <h3 className="text-2xl font-bold mb-3 group-hover:text-primary transition-colors">{course.title}</h3>
                    <p className="text-muted-foreground mb-6 flex-grow">{course.short_description || "A comprehensive curriculum designed to teach the fundamentals."}</p>
                    <div className="flex justify-between items-center pt-4 border-t border-border">
                      <span className="text-sm font-medium bg-secondary/20 text-secondary-foreground px-3 py-1 rounded-full">
                        {course.duration}
                      </span>
                      {course.monthly_fee && (
                        <span className="font-bold text-primary">₹{(course.monthly_fee / 100).toFixed(2)} / mo</span>
                      )}
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
