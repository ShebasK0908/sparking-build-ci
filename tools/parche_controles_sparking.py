#!/usr/bin/env python3
"""Parche de controles para Dragon Ball Sparking! Zero (aplicado al clon de
nxnative antes de compilar, DESPUÉS de tools/traducir_y_ajustes.py, que ya
pone el lanzador en español y los ajustes de rendimiento):

Controles táctiles con el diseño del usuario (el overlay del port móvil de
sus capturas, geometría MEDIDA sobre su foto oscura de referencia y mapa de
funciones verificado contra la tabla Standard oficial), SOLO para Sparking
(DM_GAME_ID 010035F022078000), dentro de dm/ios/Sources/DmGamepad.m.

Estilo de dibujo: el de FÁBRICA de DmIOS (petición del usuario, 2026-11-15:
«que se vean con este tipo de transparencia... bien dibujados») — las teclas
son las formas de la propia app con sus colores de fábrica y los pictogramas
del usuario van como capas de arte: siluetas blancas limpias extraídas de
sus capturas (sprites PNG en tools/sprites/*.b64), nada de recortes de foto.

Disposición (fracciones de la rect de controles, medidas de su foto):
- Rueda abajo-izquierda = stick izquierdo (moverse/volar). Pulsar el pomo
  sin moverlo = R3 (Revenge Counter); si el dedo se mueve, el toque se
  convierte en stick normal. La cámara va con el stick derecho de fábrica
  del layout completo (arrastrar en el tercio derecho sin tocar un botón).
- Chevrones = L (subir/saltar) · figura con remolino = ZL (bajar).
- Puño = Y (golpes/Smash) · ráfaga = X (Ki Blast) · cabeza con aura = A
  (Super Perception) · corredor = B (Step/dash) — vía faceAt, con sus
  centros y radios medidos (no en diamante).
- Escudo = R (guardia) · llama = ZR (cargar Ki / Sparking).
- Fila inferior = paneles de la cruceta: aura = Arriba (transformación),
  dos luchadores = Izquierda (cambio), dragón = Abajo (gestos).
- Arriba: II = + (pausa); ▶ y SKIP = segundas zonas de + (reanudar / saltar
  la cinemática desde el menú de pausa); ← = segunda zona de A (atrás en
  los menús). Son botones de interfaz del port de referencia, no del juego.
- La tuerca de ajustes de DmIOS queda DE FÁBRICA. −, L3 y los brazos de la
  cruceta de fábrica quedan ocultos y sin zona de toque en este modo.
Los índices B_* no se tocan: su orden es el de los bits DM_BTN_* del host.

Falla con error si alguna cadena esperada no aparece, para detectar cambios
de upstream. Uso: python3 parche_controles_sparking.py <ruta-al-clon>
"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
missing = []
SPRITES_DIR = Path(__file__).resolve().parent / "sprites"


def patch(relpath, pairs):
    p = root / relpath
    text = p.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            missing.append(f"{relpath}: no encontrado: {old!r}")
        else:
            text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")


def b64_literal(name):
    data = (SPRITES_DIR / f"{name}.b64").read_text(encoding="ascii").strip()
    chunks = [data[i:i + 8192] for i in range(0, len(data), 8192)]
    return " ".join(f'@"{c}"' for c in chunks)


def img_fn(fn_name, cases):
    lines = [f"static UIImage *{fn_name}(int n) {{ switch (n) {{"]
    for key, sprite in cases:
        lines.append(f"        case {key}: return sparkImg({b64_literal(sprite)});")
    lines.append("        default: return nil; } }")
    return "\n".join(lines)


GATE = r'''
// ---- Controles del usuario, solo Sparking! Zero (build privada) ----
// Diseno medido sobre la captura oscura del usuario (port movil de
// referencia) y dibujado al estilo de fabrica de DmIOS: las teclas son las
// formas de la app con sus colores, y los pictogramas del usuario son
// siluetas blancas limpias (sprites PNG incrustados en base64).
// Mapa (Standard): rueda = stick izq. (pulsar el pomo = R3, Revenge
// Counter); chevrones = L (subir); remolino = ZL (bajar); puno = Y;
// rafaga = X; cabeza con aura = A; corredor = B; escudo = R; llama = ZR
// (cargar Ki). Fila inferior = cruceta: aura = Arriba (transformacion),
// luchadores = Izquierda (cambio), dragon = Abajo (gestos). Arriba:
// II = +, play y SKIP = segundas zonas de +, flecha = segunda zona de A
// (atras en menus). La tuerca queda de fabrica; -, L3 y los brazos de la
// cruceta de fabrica quedan ocultos y sin toque en este modo.
// Los indices B_* no se tocan: su orden es el de DM_BTN_*.
// Todo vive tras este gate; el resto de juegos queda igual.
#ifndef DM_GAME_ID
#define DM_GAME_ID ""
#endif
static BOOL sparkPad(void) { return !strcmp(DM_GAME_ID, "010035F022078000"); }
static const int k_sparkZoneBit[6] = {B_PLUS, B_PLUS, B_A, B_UP, B_LEFT, B_DOWN};   // zonas: play, SKIP, atras, panel aura, panel cambio, panel dragon
static UIImage *sparkImg(NSString *b64) { NSData *d = [[NSData alloc] initWithBase64EncodedString:b64 options:0]; return d ? [UIImage imageWithData:d] : nil; }
'''

GATE += img_fn("sparkArtFor", [
    ("B_Y", "fist"), ("B_X", "burst"), ("B_A", "aura"), ("B_B", "runner"),
    ("B_L", "ascend"), ("B_ZL", "descend"), ("B_R", "shield"), ("B_ZR", "flame"),
    ("B_PLUS", "pause"),
]) + "\n"
GATE += img_fn("sparkZoneArtFor", [
    (0, "play"), (1, "skip"), (2, "back"),
    (3, "panel_aura"), (4, "panel_start"), (5, "panel_dragon"),
]) + "\n"
GATE += img_fn("sparkArtNamed", [(0, "wheel")]) + "\n"

HELPERS = r'''- (BOOL)sparkActive { return sparkPad() && !_tap && !_layout.separated; }
- (CGPoint)sparkFaceCenter:(int)b { CGRect c = _layout.controls; CGFloat x = CGRectGetMinX(c), y = CGRectGetMinY(c), w = c.size.width, h = c.size.height;
    switch (b) { case B_Y: return CGPointMake(x + 0.7746 * w, y + 0.8211 * h);
        case B_X: return CGPointMake(x + 0.6841 * w, y + 0.7309 * h);
        case B_A: return CGPointMake(x + 0.8731 * w, y + 0.6327 * h);
        default: return CGPointMake(x + 0.6567 * w, y + 0.9025 * h); } }   // B_B
- (CGFloat)sparkFaceR:(int)b { CGFloat w = _layout.controls.size.width; return b == B_Y ? 0.0448 * w : 0.0357 * w; }
- (CGPoint)sparkDropCenter:(int)b { CGRect c = _layout.controls; CGFloat x = CGRectGetMinX(c), y = CGRectGetMinY(c), w = c.size.width, h = c.size.height;
    switch (b) { case B_L: return CGPointMake(x + 0.1161 * w, y + 0.3388 * h);
        case B_ZL: return CGPointMake(x + 0.1161 * w, y + 0.5352 * h);
        case B_R: return CGPointMake(x + 0.7645 * w, y + 0.6327 * h);
        default: return CGPointMake(x + 0.8632 * w, y + 0.3208 * h); } }   // B_ZR
- (CGFloat)sparkDropR:(int)b { CGFloat w = _layout.controls.size.width;
    switch (b) { case B_L: return 0.0381 * w; case B_ZR: return 0.0398 * w; default: return 0.0365 * w; } }
- (CGPoint)sparkZoneCenter:(int)z { CGRect c = _layout.controls; CGFloat x = CGRectGetMinX(c), y = CGRectGetMinY(c), w = c.size.width, h = c.size.height;
    switch (z) { case 0: return CGPointMake(x + 0.2886 * w, y + 0.1064 * h);   // play
        case 1: return CGPointMake(x + 0.9079 * w, y + 0.1064 * h);   // SKIP
        case 2: return CGPointMake(x + 0.7968 * w, y + 0.1064 * h);   // atras
        case 3: return CGPointMake(x + 0.3897 * w, y + 0.9085 * h);   // panel aura (Arriba)
        case 4: return CGPointMake(x + 0.4710 * w, y + 0.9085 * h);   // panel cambio (Izquierda)
        default: return CGPointMake(x + 0.5522 * w, y + 0.9085 * h); } }   // panel dragon (Abajo)
- (CGFloat)sparkZoneR:(int)z { return (z < 3 ? 0.0315 : 0.0249) * _layout.controls.size.width; }
- (int)sparkZoneAt:(CGPoint)p { for (int z = 0; z < 6; z++) if (dist(p, [self sparkZoneCenter:z]) <= [self sparkZoneR:z] * (z < 3 ? 1.2 : 1.3)) return z; return -1; }
- (CGFloat)sparkKnobR { return 0.0257 * _layout.controls.size.width; }
'''

ART_INIT = r'''        if (sparkPad()) {
            for (int b = 0; b < B_N; b++) { UIImage *im = sparkArtFor(b); if (im) { _art[b] = [CALayer layer]; _art[b].contents = (id)im.CGImage; _art[b].contentsGravity = kCAGravityResize; _art[b].hidden = YES; [_key[b] addSublayer:_art[b]]; } }
            _artWheel = [CALayer layer]; _artWheel.contents = (id)sparkArtNamed(0).CGImage; _artWheel.contentsGravity = kCAGravityResize; _artWheel.hidden = YES; [_controls insertSublayer:_artWheel below:_knob];
            for (int z = 0; z < 6; z++) { _zoneKey[z] = shape(_controls); _zoneKey[z].hidden = YES; _zoneArt[z] = [CALayer layer]; _zoneArt[z].contents = (id)sparkZoneArtFor(z).CGImage; _zoneArt[z].contentsGravity = kCAGravityResize; [_zoneKey[z] addSublayer:_zoneArt[z]]; }
        }
'''

LAYOUT_BLOCK = r'''    if ([self sparkActive]) {
        for (int b = 0; b < B_N; b++) if (_label[b]) _label[b].hidden = YES;
        for (int b = B_A; b <= B_Y; b++) { CGPoint c = [self facePos:b]; CGFloat r = [self sparkFaceR:b]; setPath(_key[b], circlePath(c, r)); if (_art[b]) _art[b].frame = CGRectMake(c.x - r, c.y - r, 2 * r, 2 * r); }
        static const int dr[4] = {B_L, B_ZL, B_R, B_ZR};
        for (int i = 0; i < 4; i++) { int b = dr[i]; CGPoint c = [self dropCenter:b]; CGFloat r = [self dropR:b]; setPath(_key[b], circlePath(c, r)); if (_art[b]) _art[b].frame = CGRectMake(c.x - r, c.y - r, 2 * r, 2 * r); }
        { CGRect rc = [self pillRect:B_PLUS]; CGPoint c = CGPointMake(CGRectGetMidX(rc), CGRectGetMidY(rc)); CGFloat r = rc.size.width / 2; setPath(_key[B_PLUS], circlePath(c, r)); if (_art[B_PLUS]) _art[B_PLUS].frame = CGRectMake(c.x - r, c.y - r, 2 * r, 2 * r); }
        for (int z = 0; z < 6; z++) { CGPoint c = [self sparkZoneCenter:z]; CGFloat r = [self sparkZoneR:z]; setPath(_zoneKey[z], circlePath(c, r)); _zoneArt[z].frame = CGRectMake(c.x - r, c.y - r, 2 * r, 2 * r); }
        { CGPoint hc = self.stickHome; CGFloat hr = [self stickR:0]; _artWheel.frame = CGRectMake(hc.x - hr, hc.y - hr, 2 * hr, 2 * hr); }
        CGFloat kr = [self sparkKnobR]; _knob.bounds = CGRectMake(0, 0, 2 * kr, 2 * kr); setPath(_knob, circlePath(CGPointMake(kr, kr), kr));
        CAShapeLayer *kin = (CAShapeLayer *)_knob.sublayers.firstObject; CGPathRef kip = circlePath(CGPointMake(kr, kr), kr * 0.62); kin.frame = _knob.bounds; kin.path = kip; CGPathRelease(kip);
    }
'''

GP = "dm/ios/Sources/DmGamepad.m"

patch(GP, [
    # gate con los sprites, tras la lista de teclas bloqueadas
    ("static const int k_btns[] = {B_ZL, B_L, B_ZR, B_R, B_MINUS, B_PLUS, B_LS, B_RS};   // keys locked at touch-down (L3 / R3 only in the 3D layout)",
     "static const int k_btns[] = {B_ZL, B_L, B_ZR, B_R, B_MINUS, B_PLUS, B_LS, B_RS};   // keys locked at touch-down (L3 / R3 only in the 3D layout)" + GATE),
    # capas nuevas: arte por tecla, zonas extra, arte de la rueda, toque del pomo
    ("    CAShapeLayer *_key[B_N]; CATextLayer *_label[B_N];   // one layer per key",
     """    CAShapeLayer *_key[B_N]; CATextLayer *_label[B_N];   // one layer per key
    CALayer *_art[B_N];   // pictogramas del usuario sobre cada tecla (solo Sparking)
    CAShapeLayer *_zoneKey[6]; CALayer *_zoneArt[6]; BOOL _zoneOn[6];   // zonas extra (solo Sparking)
    CALayer *_artWheel;   // flechas de la rueda (solo Sparking)
    UITouch *_knobTouch;   // toque que pulsa el pomo (R3) en el modo Sparking"""),
    # creacion del arte tras crear las teclas
    ("""        for (int b = 0; b < B_N; b++) {
            _key[b] = shape(_controls);
            if (names[b]) _label[b] = label(_key[b], names[b]);   // the D-pad arms carry no label
        }""",
     """        for (int b = 0; b < B_N; b++) {
            _key[b] = shape(_controls);
            if (names[b]) _label[b] = label(_key[b], names[b]);   // the D-pad arms carry no label
        }
""" + ART_INIT),
    # visibilidad: en Sparking se ve su layout en 2D y 3D; -, L3/R3 y brazos ocultos
    ("""    for (int b = 0; b < B_N; b++) _key[b].hidden = _tap || (fullOnly(b) && !_full);
    _ring.hidden = _knob.hidden = _tap;""",
     """    BOOL sp = [self sparkActive];
    for (int b = 0; b < B_N; b++) { _key[b].hidden = _tap || (sp ? (b == B_MINUS || b == B_LS || b == B_RS || b >= B_LEFT) : (fullOnly(b) && !_full)); if (_art[b]) _art[b].hidden = _key[b].hidden; }
    _ring.hidden = _knob.hidden = _tap;
    if (_artWheel) _artWheel.hidden = _tap || !sp;
    for (int z = 0; z < 6; z++) if (_zoneKey[z]) _zoneKey[z].hidden = _tap || !sp;"""),
    # botones de cara en su sitio medido (no en diamante)
    ("- (CGPoint)facePos:(int)b { CGPoint c = self.faceCenter; CGFloat g = self.faceGap;",
     "- (CGPoint)facePos:(int)b { if ([self sparkActive]) return [self sparkFaceCenter:b]; CGPoint c = self.faceCenter; CGFloat g = self.faceGap;"),
    # faceAt con los radios de cada boton medido
    ("""- (uint64_t)faceAt:(CGPoint)p {   // keys under the finger in the diamond (between two keys both count)
    uint64_t m = 0; CGFloat r = self.faceHitR;""",
     """- (uint64_t)faceAt:(CGPoint)p {   // keys under the finger in the diamond (between two keys both count)
    if ([self sparkActive]) { uint64_t m = 0;
        for (int b = B_A; b <= B_Y; b++) if (dist(p, [self facePos:b]) <= [self sparkFaceR:b] * 1.12) m |= 1ull << b;
        return m; }
    uint64_t m = 0; CGFloat r = self.faceHitR;"""),
    # stick izquierdo en el sitio de la rueda, con su radio medido
    ("- (CGPoint)stickHome {\n    if (self.portraitControls) {",
     "- (CGPoint)stickHome {\n    if ([self sparkActive]) { CGRect c = _layout.controls; return CGPointMake(CGRectGetMinX(c) + 0.1119 * c.size.width, CGRectGetMinY(c) + 0.8201 * c.size.height); }\n    if (self.portraitControls) {"),
    ("- (CGFloat)stickR:(int)i { return (i ? K_RSTICK_R : K_STICK_R) * self.u; }",
     "- (CGFloat)stickR:(int)i { if ([self sparkActive] && i == 0) return 0.0697 * _layout.controls.size.width; return (i ? K_RSTICK_R : K_STICK_R) * self.u; }"),
    # hombros en sus centros medidos
    ("- (CGPoint)dropCenter:(int)b { CGRect s = self.safe; CGFloat u = self.u; BOOL z = b == B_ZL || b == B_ZR;",
     "- (CGPoint)dropCenter:(int)b { if ([self sparkActive]) return [self sparkDropCenter:b]; CGRect s = self.safe; CGFloat u = self.u; BOOL z = b == B_ZL || b == B_ZR;"),
    ("- (CGFloat)dropR:(int)b { return (b == B_ZL || b == B_ZR ? K_ZL_R : K_L_R) * self.u; }",
     "- (CGFloat)dropR:(int)b { if ([self sparkActive]) return [self sparkDropR:b]; return (b == B_ZL || b == B_ZR ? K_ZL_R : K_L_R) * self.u; }"),
    # + en el sitio del boton II de la referencia (la tuerca queda entre medias, de fabrica)
    ("- (CGRect)pillRect:(int)b { CGRect s = self.safe;",
     """- (CGRect)pillRect:(int)b { if ([self sparkActive] && b == B_PLUS) { CGRect c = _layout.controls; CGFloat side = 0.0630 * c.size.width; CGPoint ctr = CGPointMake(CGRectGetMinX(c) + 0.1716 * c.size.width, CGRectGetMinY(c) + 0.1064 * c.size.height); return CGRectMake(ctr.x - side / 2, ctr.y - side / 2, side, side); } CGRect s = self.safe;"""),
    # metodos auxiliares, antes de menuDistance (la tuerquita NO se toca)
    ("- (CGFloat)menuDistance:(CGPoint)p {",
     HELPERS + "- (CGFloat)menuDistance:(CGPoint)p {"),
    # -, L3 y R3 sin zona de toque en este modo
    ("""- (CGFloat)buttonDistance:(int)b point:(CGPoint)p {
    CGFloat u = self.u;""",
     """- (CGFloat)buttonDistance:(int)b point:(CGPoint)p {
    CGFloat u = self.u;
    if ([self sparkActive] && (isClick(b) || b == B_MINUS)) return CGFLOAT_MAX;"""),
    ("        if (fullOnly(b) && !_full) continue;",
     "        if ((fullOnly(b) && !_full) || ([self sparkActive] && (isClick(b) || b == B_MINUS))) continue;"),
    # controlAt: zonas, pomo y cara reclaman su toque
    ("    if ([self btnAt:p] >= 0) return YES;",
     "    if ([self btnAt:p] >= 0) return YES;\n    if ([self sparkActive] && ([self sparkZoneAt:p] >= 0 || dist(p, self.stickHome) <= [self sparkKnobR] * 1.25)) return YES;"),
    ("    if (dist(p, self.faceCenter) / (self.faceGap + MAX(self.faceR * 1.6, self.faceHitR)) <= 1) return YES;",
     "    if ([self sparkActive] && [self faceAt:p]) return YES;\n    if (dist(p, self.faceCenter) / (self.faceGap + MAX(self.faceR * 1.6, self.faceHitR)) <= 1) return YES;"),
    ("    if (_full && dist(p, self.dpadCenter) / MAX(self.dpadR * K_DPAD_GRAB, _layout.separated ? 22 : 0) < 1) return YES;",
     "    if (_full && ![self sparkActive] && dist(p, self.dpadCenter) / MAX(self.dpadR * K_DPAD_GRAB, _layout.separated ? 22 : 0) < 1) return YES;"),
    ("    return _full && !_stick[1] && [self inRightArea:p];",
     "    return (_full || [self sparkActive]) && !_stick[1] && [self inRightArea:p];"),
    # touchesBegan: pomo (R3) y zonas se reclaman antes que el resto
    ("        int hit = _tap ? -1 : [self btnAt:p];   // the menu button took its own touches (menuTakes)",
     """        if ([self sparkActive]) {
            if (!_stick[0] && !_knobTouch && dist(p, self.stickHome) <= [self sparkKnobR] * 1.25) { [_owner setObject:@(C_BTN | (uint64_t)B_RS << 8) forKey:t]; _knobTouch = t; continue; }
            int z = [self sparkZoneAt:p];
            if (z >= 0) { [_owner setObject:@(C_BTN | (uint64_t)k_sparkZoneBit[z] << 8) forKey:t]; continue; }
        }
        int hit = _tap ? -1 : [self btnAt:p];   // the menu button took its own touches (menuTakes)"""),
    # touchesBegan: la cara reclama si faceAt acierta; la cruceta de fabrica no
    ("        CGFloat f = dist(p, self.faceCenter) / (self.faceGap + MAX(self.faceR * 1.6, self.faceHitR)); if (f <= best) { best = f; kind = C_FACE; }",
     "        if ([self sparkActive] && [self faceAt:p]) { best = 0; kind = C_FACE; }\n        CGFloat f = dist(p, self.faceCenter) / (self.faceGap + MAX(self.faceR * 1.6, self.faceHitR)); if (f <= best) { best = f; kind = C_FACE; }"),
    ("        if (_full) { CGFloat d = dist(p, self.dpadCenter) / MAX(self.dpadR * K_DPAD_GRAB, _layout.separated ? 22 : 0); if (d < best) { best = d; kind = C_DPAD; } }",
     "        if (_full && ![self sparkActive]) { CGFloat d = dist(p, self.dpadCenter) / MAX(self.dpadR * K_DPAD_GRAB, _layout.separated ? 22 : 0); if (d < best) { best = d; kind = C_DPAD; } }"),
    # touchesBegan: el stick derecho (camara) tambien en el layout 2D de Sparking
    ("        if (kind == C_NONE && _full && !_stick[1] && [self inRightArea:p]) { kind = C_STICK; idx = 1; _rCentre = p; }   // the right stick: centred where the touch lands",
     "        if (kind == C_NONE && (_full || [self sparkActive]) && !_stick[1] && [self inRightArea:p]) { kind = C_STICK; idx = 1; _rCentre = p; }   // the right stick: centred where the touch lands"),
    # touchesMoved: si el toque del pomo se mueve, se convierte en stick izquierdo
    ("        uint64_t v = [_owner objectForKey:t].unsignedLongLongValue; int c = (int)(v & 0xff); CGPoint p = [t locationInView:self];\n        if (c == C_FACE) [_faceOf setObject:@([self faceAt:p]) forKey:t];",
     """        uint64_t v = [_owner objectForKey:t].unsignedLongLongValue; int c = (int)(v & 0xff); CGPoint p = [t locationInView:self];
        if ([self sparkActive] && _knobTouch == t && dist(p, self.stickHome) > 14) { _knobTouch = nil; [_owner setObject:@(C_STICK) forKey:t]; _stick[0] = t; _stickNow[0] = p; v = C_STICK; c = C_STICK; }
        if (c == C_FACE) [_faceOf setObject:@([self faceAt:p]) forKey:t];"""),
    # fin de toques y reset: soltar el pomo
    ("        [_owner removeObjectForKey:t]; [_faceOf removeObjectForKey:t]; for (int i = 0; i < 2; i++) if (t == _stick[i]) _stick[i] = nil;",
     "        if (t == _knobTouch) _knobTouch = nil;\n        [_owner removeObjectForKey:t]; [_faceOf removeObjectForKey:t]; for (int i = 0; i < 2; i++) if (t == _stick[i]) _stick[i] = nil;"),
    ("- (void)reset { [_owner removeAllObjects]; [_faceOf removeAllObjects]; _stick[0] = _stick[1] = nil;",
     "- (void)reset { _knobTouch = nil; [_owner removeAllObjects]; [_faceOf removeAllObjects]; _stick[0] = _stick[1] = nil;"),
    # refresh: que zona esta pulsada segun donde esta el dedo (cada una se ilumina sola)
    ("""- (void)refresh {   // pressed state → fill, sticks → knob position
    uint64_t all = _faceBits | _dpadBits | _btnBits;""",
     """- (void)refresh {   // pressed state → fill, sticks → knob position
    uint64_t all = _faceBits | _dpadBits | _btnBits;
    BOOL sp = [self sparkActive];
    if (sp) { for (int z = 0; z < 6; z++) _zoneOn[z] = NO;
        for (UITouch *t in _owner) { uint64_t v = [_owner objectForKey:t].unsignedLongLongValue; if ((int)(v & 0xff) == C_BTN) { int bit = (int)(v >> 8); CGPoint p = [t locationInView:self];
            for (int z = 0; z < 6; z++) if (k_sparkZoneBit[z] == bit && dist(p, [self sparkZoneCenter:z]) <= [self sparkZoneR:z] * 1.3) _zoneOn[z] = YES; } } }"""),
    # refresh: el arte se encoge un poco al pulsar (la pulsacion se nota)
    ("        _key[b].fillColor = (on ? k_on : k_idle).CGColor; _label[b].foregroundColor = (on ? k_textOn : k_text).CGColor; }",
     "        _key[b].fillColor = (on ? k_on : k_idle).CGColor; _label[b].foregroundColor = (on ? k_textOn : k_text).CGColor; if (_art[b]) _art[b].transform = (sp && on) ? CATransform3DMakeScale(0.93, 0.93, 1) : CATransform3DIdentity; }"),
    # refresh: relleno de las zonas y del pomo pulsado
    ("    _knob.position = CGPointMake(h.x + o.x, h.y + o.y); _knob.fillColor = (_stick[0] ? k_on : k_idle).CGColor;",
     """    _knob.position = CGPointMake(h.x + o.x, h.y + o.y); _knob.fillColor = (_stick[0] ? k_on : k_idle).CGColor;
    if (sp) { for (int z = 0; z < 6; z++) _zoneKey[z].fillColor = (_zoneOn[z] ? k_on : k_idle).CGColor; if (_knobTouch) _knob.fillColor = k_on.CGColor; }"""),
    # dibujo Sparking al final de layoutSubviews
    ("    [CATransaction commit];\n    [self refresh];\n}",
     LAYOUT_BLOCK + "    [CATransaction commit];\n    [self refresh];\n}"),
])

if missing:
    print("FALTAN PATRONES (¿cambió upstream?):")
    for m in missing:
        print(" -", m)
    sys.exit(1)
print("Parche aplicado: controles del usuario para Sparking! Zero (estilo fábrica).")
