import os
import sys
import uuid
import random
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy import text

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.profile import Profile
from app.models.lesson import Lesson
from app.models.song import Song

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_database():
    print("Starting database seed...")
    db = SessionLocal()
    
    print("Clearing tables manually...")
    db.execute(text("TRUNCATE TABLE users CASCADE"))
    db.commit()

    # 1. Create Admin
    admin = User(
        email="admin@melodix.app",
        password_hash=get_password_hash("admin123"),
        full_name="System Admin",
        role="ADMIN",
        onboarding_completed=True
    )
    db.add(admin)

    # 2. Create Teachers
    teachers = [
        User(email="sarah.jenkins@melodix.app", password_hash=get_password_hash("teacher123"), full_name="Sarah Jenkins", role="TEACHER", onboarding_completed=True),
        User(email="david.chen@melodix.app", password_hash=get_password_hash("teacher123"), full_name="David Chen", role="TEACHER", onboarding_completed=True)
    ]
    db.add_all(teachers)
    
    # 3. Create Students
    students = [
        User(email=f"student{i}@example.com", password_hash=get_password_hash("student123"), full_name=f"Student {i}", role="STUDENT", onboarding_completed=True)
        for i in range(1, 11)
    ]
    db.add_all(students)
    db.commit()

    # Create Profiles
    all_users = [admin] + teachers + students
    for u in all_users:
        profile = Profile(
            user_id=u.id,
            bio=f"Hello, I am {u.full_name}. I love music!",
            skill_level="INTERMEDIATE" if u.role == "TEACHER" else "BEGINNER",
            preferred_instrument="Piano",
            daily_practice_goal=30 if u.role == "STUDENT" else 0,
            preferred_genres=["Classical", "Jazz", "Pop"],
            learning_preferences={"tempo": "slow", "feedback_style": "encouraging"}
        )
        db.add(profile)
    
    # 4. Create Songs
    songs_data = [
        ("Fur Elise", "Ludwig van Beethoven", "Classical", "INTERMEDIATE", 110, "A minor", "3/8"),
        ("Moonlight Sonata", "Ludwig van Beethoven", "Classical", "ADVANCED", 60, "C# minor", "2/2"),
        ("Minuet in G", "J.S. Bach", "Classical", "BEGINNER", 120, "G major", "3/4"),
        ("Bohemian Rhapsody", "Queen", "Rock", "ADVANCED", 72, "Bb major", "4/4"),
        ("Let It Be", "The Beatles", "Pop", "BEGINNER", 70, "C major", "4/4"),
        ("Maple Leaf Rag", "Scott Joplin", "Jazz", "ADVANCED", 90, "Ab major", "2/4"),
        ("Clair de Lune", "Claude Debussy", "Classical", "ADVANCED", 65, "Db major", "9/8"),
        ("Imagine", "John Lennon", "Pop", "BEGINNER", 76, "C major", "4/4"),
        ("Take Five", "Dave Brubeck", "Jazz", "INTERMEDIATE", 174, "Eb minor", "5/4"),
        ("Hallelujah", "Leonard Cohen", "Pop", "BEGINNER", 80, "C major", "6/8")
    ]
    
    songs = []
    for title, composer, genre, diff, bpm, key, time_sig in songs_data:
        s = Song(
            title=title, composer=composer, genre=genre, difficulty=diff,
            bpm=bpm, key_signature=key, time_signature=time_sig, duration=random.randint(120, 360)
        )
        songs.append(s)
        db.add(s)
    db.commit()
    
    # 5. Create Lessons (25 Lessons spanning different categories, genres, difficulty levels)
    # Using structured objectives: [{"id": "...", "title": "...", "description": "..."}]
    categories = ["Theory", "Technique", "Repertoire", "Sight Reading"]
    difficulties = ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
    genres = ["Classical", "Jazz", "Pop", "Rock"]

    lessons_data = [
        # Theory Lessons
        ("Introduction to C Major Scale", "c-major-scale-intro", "Learn the construction and layout of the C Major scale on the keyboard.", "Theory", "BEGINNER", "Classical", 15, 1, [
            {"id": "c-maj-obj-1", "title": "Understand half and whole steps", "description": "Learn the W-W-H-W-W-W-H pattern"},
            {"id": "c-maj-obj-2", "title": "Locate white keys", "description": "Identify all C, D, E, F, G, A, B keys"}
        ]),
        ("Understanding Major Triads", "understanding-major-triads", "How to build major chords in root position.", "Theory", "BEGINNER", "Pop", 20, 2, [
            {"id": "triad-obj-1", "title": "Build a triad using thirds", "description": "Stack a major third and a minor third"}
        ]),
        ("Circle of Fifths Basics", "circle-of-fifths-basics", "Introduction to key signatures and relations.", "Theory", "INTERMEDIATE", "Classical", 25, 3, [
            {"id": "fifths-obj-1", "title": "Recognize key signature order", "description": "Learn order of sharps and flats"}
        ]),
        ("Minor Scales Explained", "minor-scales-explained", "Natural, harmonic, and melodic minor scales.", "Theory", "INTERMEDIATE", "Classical", 30, 4, [
            {"id": "minor-obj-1", "title": "Identify minor scale types", "description": "Differentiate natural, harmonic, melodic"}
        ]),
        ("Seventh Chords in Jazz", "seventh-chords-in-jazz", "Major, minor, dominant, and half-diminished seventh chords.", "Theory", "ADVANCED", "Jazz", 35, 5, [
            {"id": "seventh-obj-1", "title": "Construct dominant 7ths", "description": "Build dominants on the 5th scale degree"}
        ]),
        ("Modal Interchange", "modal-interchange-advanced", "Borrowing chords from parallel keys for rich progressions.", "Theory", "ADVANCED", "Pop", 40, 6, [
            {"id": "modal-obj-1", "title": "Identify borrowed chords", "description": "Spot IV-iv transitions in chord progressions"}
        ]),

        # Technique Lessons
        ("Finger Independence Exercises", "finger-independence-1", "Simple exercises to build finger autonomy.", "Technique", "BEGINNER", "Classical", 10, 1, [
            {"id": "finger-obj-1", "title": "Five-finger pattern fluidity", "description": "Play legato pattern without raising adjacent fingers"}
        ]),
        ("Introduction to Arpeggios", "arpeggios-intro", "Flowing hand-over-hand arpeggios across octaves.", "Technique", "INTERMEDIATE", "Classical", 20, 2, [
            {"id": "arp-obj-1", "title": "Thumb tuck technique", "description": "Pass thumb smoothly under fingers"}
        ]),
        ("Hanon Exercise No. 1", "hanon-exercise-1", "The ultimate warm-up to equalize finger strength.", "Technique", "BEGINNER", "Classical", 15, 3, [
            {"id": "hanon-obj-1", "title": "Maintain even tempo", "description": "Use metronome at 60BPM"}
        ]),
        ("Building Wrist Flexibility", "wrist-flexibility", "Avoid tension by incorporating wrist rotation.", "Technique", "INTERMEDIATE", "Classical", 15, 4, [
            {"id": "wrist-obj-1", "title": "Implement wrist circles", "description": "Rotate wrists during scale transitions"}
        ]),
        ("Mastering Trills and Ornaments", "mastering-trills", "Advanced exercises for fast trills and clear execution.", "Technique", "ADVANCED", "Classical", 30, 5, [
            {"id": "trill-obj-1", "title": "Achieve velocity in trills", "description": "Trill evenly at 120BPM"}
        ]),
        ("Octave Jump Agility", "octave-jump-agility", "Accurate wide jumps across the keyboard without looking.", "Technique", "ADVANCED", "Classical", 35, 6, [
            {"id": "jump-obj-1", "title": "Blind target placement", "description": "Hit octaves cleanly using peripheral vision"}
        ]),

        # Repertoire Lessons
        ("Minuet in G Walkthrough", "minuet-in-g-walkthrough", "Learn J.S. Bach's beginner classical favorite.", "Repertoire", "BEGINNER", "Classical", 30, 1, [
            {"id": "minuet-obj-1", "title": "Play first section hands-together", "description": "Sync LH quarter notes with RH eighth notes"}
        ]),
        ("Let It Be Chord Accompaniment", "let-it-be-accompaniment", "Accompany yourself singing or playing this Pop classic.", "Repertoire", "BEGINNER", "Pop", 25, 2, [
            {"id": "letitbe-obj-1", "title": "Perform rhythmic comping", "description": "Play solid block chords on every beat"}
        ]),
        ("Gymnopédie No.1 Guide", "gymnopedie-no1-guide", "Master the slow, ambient pulse of Satie.", "Repertoire", "INTERMEDIATE", "Classical", 40, 3, [
            {"id": "sat-obj-1", "title": "Balance left-hand accompaniment", "description": "Keep LH bass notes soft, melody singing"}
        ]),
        ("Für Elise Section A", "fur-elise-section-a", "Learn the famous opening theme of Beethoven.", "Repertoire", "INTERMEDIATE", "Classical", 35, 4, [
            {"id": "furelise-obj-1", "title": "Execute pedal markings", "description": "Clean pedal changes on harmonic shifts"}
        ]),
        ("Clair de Lune Rubato", "clair-de-lune-rubato", "Expressive timing in Debussy's impressionist masterpiece.", "Repertoire", "ADVANCED", "Classical", 50, 5, [
            {"id": "clair-obj-1", "title": "Play polyrhythms", "description": "Sync two-against-three rhythm patterns"}
        ]),
        ("Bohemian Rhapsody Piano Solo", "bohemian-rhapsody-solo", "Arrange and play the epic rock anthem.", "Repertoire", "ADVANCED", "Rock", 60, 6, [
            {"id": "bohemian-obj-1", "title": "Manage dynamic transitions", "description": "Transition smoothly from ballad to rock opera section"}
        ]),

        # Sight Reading Lessons
        ("Sight Reading Easy Intervals", "sight-reading-intervals", "Recognizing seconds, thirds, and fifths on sight.", "Sight Reading", "BEGINNER", "Classical", 15, 1, [
            {"id": "sight-int-obj-1", "title": "Identify intervals instantly", "description": "Differentiate step vs skip"}
        ]),
        ("Rhythmic Sight Reading 1", "rhythmic-sight-reading-1", "Tapping and reading basic quarter and eighth note patterns.", "Sight Reading", "BEGINNER", "Pop", 10, 2, [
            {"id": "rhythm-obj-1", "title": "Keep constant beat", "description": "Tap foot while reading rhythm sheet"}
        ]),
        ("Reading Ledger Lines", "reading-ledger-lines", "Demystifying notes high above and below the grand staff.", "Sight Reading", "INTERMEDIATE", "Classical", 20, 3, [
            {"id": "ledger-obj-1", "title": "Locate high C keys", "description": "Instantly name ledger-line notes up to 3 lines"}
        ]),
        ("Key Signature Sight Reading", "key-signature-sight-reading", "How to scan the key signature first and maintain accidentals.", "Sight Reading", "INTERMEDIATE", "Classical", 25, 4, [
            {"id": "keysig-obj-1", "title": "Scan key signatures", "description": "Play in F Major automatically keeping all Bb notes"}
        ]),
        ("Complex Rhythms Reading", "complex-rhythms-sight-reading", "Sight reading syncopations and dotted eighth notes.", "Sight Reading", "ADVANCED", "Jazz", 30, 5, [
            {"id": "complex-obj-1", "title": "Sight read syncopations", "description": "Read off-beat ties accurately at 80BPM"}
        ]),
        ("Dual Clef Coordination", "dual-clef-coordination", "Reading active lines in both hands simultaneously.", "Sight Reading", "ADVANCED", "Classical", 35, 6, [
            {"id": "dual-obj-1", "title": "Track bass and treble lines", "description": "Perform sight reading of counterpoint lines"}
        ])
    ]

    for title, slug, desc, cat, diff, gen, dur, order, objs in lessons_data:
        # Distribute lessons between the two teachers
        teacher = teachers[0] if len(db.query(Lesson).filter(Lesson.teacher_id == teachers[0].id).all()) < 12 else teachers[1]
        
        l = Lesson(
            teacher_id=teacher.id,
            title=title,
            slug=slug,
            description=desc,
            category=cat,
            difficulty=diff,
            genre=gen,
            estimated_duration=dur,
            display_order=order,
            objectives=objs,
            visibility="PUBLIC",
            is_published=True,
            published_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        
        # Link some relevant songs to Repertoire lessons
        if "Minuet" in title:
            minuet_song = db.query(Song).filter(Song.title == "Minuet in G").first()
            if minuet_song:
                l.songs.append(minuet_song)
        elif "Elise" in title:
            elise_song = db.query(Song).filter(Song.title == "Fur Elise").first()
            if elise_song:
                l.songs.append(elise_song)
        elif "Lune" in title:
            lune_song = db.query(Song).filter(Song.title == "Clair de Lune").first()
            if lune_song:
                l.songs.append(lune_song)
        elif "Moonlight" in title:
            moon_song = db.query(Song).filter(Song.title == "Moonlight Sonata").first()
            if moon_song:
                l.songs.append(moon_song)
        elif "Bohemian" in title:
            rhapsody_song = db.query(Song).filter(Song.title == "Bohemian Rhapsody").first()
            if rhapsody_song:
                l.songs.append(rhapsody_song)
        elif "Let It" in title:
            letitbe_song = db.query(Song).filter(Song.title == "Let It Be").first()
            if letitbe_song:
                l.songs.append(letitbe_song)

        db.add(l)
    
    db.commit()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()
