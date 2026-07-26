import { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { SongCard } from '../components/SongCard';
import { lessonsApi } from '../api/lessons';
import type { Lesson } from '../api/lessons';
import { useUser } from '../context/UserContext';
import styles from './Learn.module.css';

interface CategoryGroup {
  title: string;
  songs: Lesson[];
}

export function Learn() {
  const { profile } = useUser();
  const [categories, setCategories] = useState<CategoryGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchLessons = async () => {
      try {
        setLoading(true);
        const data = await lessonsApi.getLessons({ search: searchTerm });
        
        // Group by category
        const grouped: Record<string, Lesson[]> = {};
        data.items.forEach(lesson => {
          const cat = lesson.category || 'Other';
          if (!grouped[cat]) grouped[cat] = [];
          grouped[cat].push(lesson);
        });
        
        const cats = Object.entries(grouped)
          .map(([title, songs]) => ({
            title,
            songs: songs.sort((a, b) => a.display_order - b.display_order)
          }))
          .sort((a, b) => a.title.localeCompare(b.title));
          
        setCategories(cats);
      } catch (err) {
        console.error('Failed to fetch lessons', err);
      } finally {
        setLoading(false);
      }
    };
    
    const timer = setTimeout(() => {
      fetchLessons();
    }, 300);
    
    return () => clearTimeout(timer);
  }, [searchTerm]);

  return (
    <motion.div 
      className={styles.learn}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Discover</h1>
          <p className={styles.subtitle}>Find your next favorite piece to play, {profile?.full_name?.split(' ')[0] || 'Musician'}.</p>
        </div>
        
        <div className={styles.searchContainer}>
          <Search size={20} className={styles.searchIcon} />
          <input 
            type="text" 
            className={styles.searchInput} 
            placeholder="Search lessons, categories, or genres..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </header>

      {loading ? (
        <div className={styles.loading}>Loading lessons...</div>
      ) : categories.length === 0 ? (
        <div className={styles.empty}>No lessons found.</div>
      ) : (
        <div className={styles.categories}>
          {categories.map((category) => (
            <section key={category.title} className={styles.categorySection}>
              <div className={styles.categoryHeader}>
                <h2 className={styles.categoryTitle}>{category.title}</h2>
                <Link to="#" className={styles.seeAll}>See All</Link>
              </div>
              
              <div className={styles.songList}>
                {category.songs.map((lesson) => (
                  <div key={lesson.id} className={styles.songWrapper}>
                    <SongCard
                      id={lesson.id}
                      title={lesson.title}
                      composer={lesson.genre || 'Unknown Genre'}
                      difficulty={lesson.difficulty ? lesson.difficulty.charAt(0) + lesson.difficulty.slice(1).toLowerCase() : 'Beginner'}
                      duration={`${lesson.estimated_duration || 5} min`}
                      artworkUrl={lesson.thumbnail_url || ''}
                    />
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </motion.div>
  );
}
