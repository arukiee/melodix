
import { Search } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { SongCard } from '../components/SongCard';
import { useUser } from '../context/UserContext';
import styles from './Learn.module.css';

// Mock catalog data
const baseCategories = [
  {
    title: 'Popular Classical',
    songs: [
      { id: 'moonlight', title: 'Moonlight Sonata', composer: 'Ludwig van Beethoven', difficulty: 'Advanced', duration: '15 min', artworkUrl: 'https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?q=80&w=300&auto=format&fit=crop' },
      { id: 'canon', title: 'Canon in D', composer: 'Johann Pachelbel', difficulty: 'Intermediate', duration: '5 min', artworkUrl: 'https://images.unsplash.com/photo-1507838153428-9d982a1df8e1?q=80&w=300&auto=format&fit=crop' },
      { id: 'gymnopedie', title: 'Gymnopédie No.1', composer: 'Erik Satie', difficulty: 'Intermediate', duration: '3 min', artworkUrl: 'https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?q=80&w=300&auto=format&fit=crop' },
      { id: 'nocturne', title: 'Nocturne Op. 9 No. 2', composer: 'Frédéric Chopin', difficulty: 'Advanced', duration: '4 min', artworkUrl: 'https://images.unsplash.com/photo-1558546197-29cbcfcefa43?q=80&w=300&auto=format&fit=crop' },
    ]
  },
  {
    title: 'Movie Themes',
    songs: [
      { id: 'pirates', title: "He's a Pirate", composer: 'Klaus Badelt', difficulty: 'Intermediate', duration: '3 min', artworkUrl: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=300&auto=format&fit=crop' },
      { id: 'harry-potter', title: "Hedwig's Theme", composer: 'John Williams', difficulty: 'Intermediate', duration: '2 min', artworkUrl: 'https://images.unsplash.com/photo-1618944847023-38aa001235f0?q=80&w=300&auto=format&fit=crop' },
      { id: 'lotr', title: 'Concerning Hobbits', composer: 'Howard Shore', difficulty: 'Beginner', duration: '3 min', artworkUrl: 'https://images.unsplash.com/photo-1465146344425-f00d5f5c8f07?q=80&w=300&auto=format&fit=crop' },
      { id: 'jurassic', title: 'Jurassic Park Theme', composer: 'John Williams', difficulty: 'Intermediate', duration: '3 min', artworkUrl: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=300&auto=format&fit=crop' },
    ]
  }
];

const genericPicks = {
  title: 'Beginner Essentials',
  songs: [
    { id: 'c-major-scale', title: 'C Major Scale', composer: 'Fundamentals', difficulty: 'Beginner', duration: '5 min', artworkUrl: '' },
    { id: 'twinkle', title: 'Twinkle Twinkle', composer: 'Traditional', difficulty: 'Beginner', duration: '3 min', artworkUrl: '' },
    { id: 'ode-to-joy', title: 'Ode to Joy', composer: 'Ludwig van Beethoven', difficulty: 'Beginner', duration: '4 min', artworkUrl: 'https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?q=80&w=300&auto=format&fit=crop' },
    { id: 'mary-lamb', title: 'Mary Had a Little Lamb', composer: 'Traditional', difficulty: 'Beginner', duration: '2 min', artworkUrl: '' },
  ]
};

const personalizedPicks = {
  title: 'Recommended for You',
  songs: [
    { id: 'fur-elise', title: 'Für Elise', composer: 'Ludwig van Beethoven', difficulty: 'Intermediate', duration: '4 min', artworkUrl: 'https://images.unsplash.com/photo-1552422535-c45813c61732?q=80&w=300&auto=format&fit=crop' },
    { id: 'river-flows', title: 'River Flows in You', composer: 'Yiruma', difficulty: 'Intermediate', duration: '5 min', artworkUrl: 'https://images.unsplash.com/photo-1571126771340-91fb55979dd5?q=80&w=300&auto=format&fit=crop' },
    { id: 'numb', title: 'Numb', composer: 'Linkin Park', difficulty: 'Beginner', duration: '3 min', artworkUrl: 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?q=80&w=300&auto=format&fit=crop' },
    { id: 'interstellar', title: 'Cornfield Chase', composer: 'Hans Zimmer', difficulty: 'Advanced', duration: '6 min', artworkUrl: 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=300&auto=format&fit=crop' },
  ]
};

export function Learn() {
  const { completedLessons } = useUser();
  const topCategory = completedLessons >= 7 ? personalizedPicks : genericPicks;
  const categories = [topCategory, ...baseCategories];

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
          <p className={styles.subtitle}>Find your next favorite piece to play.</p>
        </div>
        
        <div className={styles.searchContainer}>
          <Search size={20} className={styles.searchIcon} />
          <input 
            type="text" 
            className={styles.searchInput} 
            placeholder="Search songs, artists, or genres..."
          />
        </div>
      </header>

      <div className={styles.categories}>
        {categories.map((category) => (
          <section key={category.title} className={styles.categorySection}>
            <div className={styles.categoryHeader}>
              <h2 className={styles.categoryTitle}>{category.title}</h2>
              <Link to="#" className={styles.seeAll}>See All</Link>
            </div>
            
            <div className={styles.songList}>
              {category.songs.map((song) => (
                <div key={song.id} className={styles.songWrapper}>
                  <SongCard
                    id={song.id}
                    title={song.title}
                    composer={song.composer}
                    difficulty={song.difficulty}
                    duration={song.duration}
                    artworkUrl={song.artworkUrl}
                  />
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </motion.div>
  );
}
