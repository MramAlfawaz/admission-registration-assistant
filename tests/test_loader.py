from app.documents.loader import fix_ligature_order


def test_mid_word_lam_alef():
    chars = [("خ", 358.80, 366.43), ("ا", 358.80, 358.80),
             ("ل", 352.17, 358.80), ("ل", 345.08, 352.17)]
    assert fix_ligature_order(chars) == "خلال"


def test_word_start_lam_hamza():
    chars = [("ا", 266.01, 268.47), ("أ", 266.41, 266.41),
             ("ل", 260.09, 266.41), ("ر", 256.36, 260.09)]
    assert fix_ligature_order(chars) == "الأر"


def test_alef_sharing_position_is_not_swapped_wrongly():
    chars = [("ا", 456.06, 458.96), ("إ", 456.06, 456.06),
             ("ل", 450.53, 456.06), ("ن", 447.53, 450.53)]
    assert fix_ligature_order(chars) == "الإن"


def test_normal_text_unchanged():
    chars = [("ع", 456.66, 462.14), ("و", 451.81, 456.78),
             ("د", 446.67, 451.65), ("ة", 442.38, 446.67)]
    assert fix_ligature_order(chars) == "عودة"
