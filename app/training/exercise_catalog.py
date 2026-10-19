"""Built-in exercise catalog. The migration that creates `exercises` seeds a copy of this list;
ExerciseRepository.get_by_name() also inserts a missing entry from here, so the generator never
depends on seed data having been loaded."""

# name, category, is_high_impact, required_equipment, description
CATALOG = [
    ("Dynamic warm-up", "warm_up", False, None, "5 min easy jog, then leg swings, high knees, butt kicks and skips."),
    ("A-skips", "sprint", False, None, "Rhythmic skipping drill focusing on knee lift and foot strike under the hips."),
    ("Strides", "sprint", False, None, "Relaxed, gradually faster runs at 70-80% effort with full walk-back recovery."),
    ("Acceleration sprints", "sprint", True, None, "Short sprints from a standing start focusing on forward lean and powerful pushes."),
    ("Flying sprints", "sprint", True, None, "Build up over 20 m, then hold near-top speed through a short zone."),
    ("Easy run", "endurance", False, None, "Conversational pace - you can speak in full sentences. Walk breaks are fine."),
    ("Tempo run", "endurance", False, None, "Comfortably hard, steady pace you could hold for about an hour when fresh."),
    ("Run intervals", "endurance", False, None, "Repeated faster efforts with easy jog recovery between them."),
    ("Pop-up jumps", "long_jump", True, None, "Short approach, single-leg take-off, drive the knee up and land on both feet."),
    ("Standing long jump", "long_jump", True, None, "Two-foot take-off and landing. Swing arms, extend hips, land softly."),
    ("Bounding", "long_jump", True, None, "Exaggerated running strides with long ground contact and high knee drive."),
    ("High jump approach curve runs", "high_jump", False, None, "Run the J-shaped approach without jumping to rehearse rhythm and lean."),
    ("High jump take-off drill", "high_jump", True, None, "Curve approach of 3-5 steps into a vertical single-leg take-off, no bar."),
    ("Scissor jumps", "high_jump", True, "high_jump_setup", "Short approach scissor jump over a low bar or elastic onto a mat."),
    ("Fosbury flop technique jumps", "high_jump", True, "high_jump_setup", "Short-approach flop over a low bar onto a proper landing mat."),
    ("Bodyweight squat", "strength", False, None, "Controlled squat to a comfortable depth."),
    ("Goblet squat", "strength", False, "dumbbells", "Squat holding a dumbbell or kettlebell at the chest."),
    ("Romanian deadlift", "strength", False, "dumbbells", "Hip hinge with dumbbells or a barbell, slight knee bend, neutral back."),
    ("Glute bridge", "strength", False, None, "Lying on your back, drive hips up by squeezing the glutes."),
    ("Split squat", "strength", False, None, "Static lunge position, lower the back knee towards the floor. Reps per leg."),
    ("Calf raises", "strength", False, None, "Slow raises onto the toes, pause at the top, lower under control."),
    ("Plank", "strength", False, None, "Forearm plank with a straight line from head to heels."),
    ("Hip mobility flow", "mobility", False, None, "Hip circles, 90/90 switches, hip-flexor stretch and world's greatest stretch."),
    ("Ankle and calf mobility", "mobility", False, None, "Knee-to-wall ankle mobilisations and gentle calf stretches."),
    ("Easy walk", "recovery", False, None, "Relaxed walk at an easy pace."),
    ("Sprint assessment", "assessment", True, None, "Timed sprint from a standing start. Same distance, surface and timing method every time."),
    ("Long jump assessment", "assessment", True, None, "Measured standing long jump: take-off line to the back-most landing mark."),
    ("High jump assessment", "assessment", True, "high_jump_setup", "Measured bar clearance with a short approach and increasing heights."),
    ("Run assessment", "assessment", False, None, "Timed run over the assessment distance on the same route/surface every time."),
]

CATALOG_BY_NAME = {name: (category, high_impact, equipment, description) for name, category, high_impact, equipment, description in CATALOG}
HIGH_IMPACT_EXERCISES = {name for name, _, high_impact, _, _ in CATALOG if high_impact}
