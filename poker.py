import random
import os
import sys

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['Espadas', 'Copas', 'Ouros', 'Paus']
RANK_VALUES = {r: i for i, r in enumerate(RANKS)}

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def build_deck():
    return [{'rank': r, 'suit': s} for s in SUITS for r in RANKS]

def shuffle(deck):
    random.shuffle(deck)
    return deck

def card_str(card, hidden=False):
    if hidden:
        return '[??]'
    return f'[{card["rank"]}{card["suit"]}]'

def hand_str(hand, hidden=False):
    return ' '.join(card_str(c, hidden) for c in hand)

def rank_hand(hand, community):
    cards = hand + community
    ranks = sorted([RANK_VALUES[c['rank']] for c in cards], reverse=True)
    suits = [c['suit'] for c in cards]

    rank_count = {}
    for r in ranks:
        rank_count[r] = rank_count.get(r, 0) + 1

    suit_count = {}
    for s in suits:
        suit_count[s] = suit_count.get(s, 0) + 1

    counts = sorted(rank_count.values(), reverse=True)
    flush = any(v >= 5 for v in suit_count.values())

    unique_ranks = sorted(set(ranks), reverse=True)
    straight = False
    straight_high = 0
    for i in range(len(unique_ranks) - 4):
        window = unique_ranks[i:i+5]
        if window[0] - window[4] == 4 and len(set(window)) == 5:
            straight = True
            straight_high = window[0]
            break

    if straight and flush:
        return (8, straight_high, 'Straight Flush')
    if counts[0] == 4:
        quad_rank = [r for r, v in rank_count.items() if v == 4][0]
        return (7, quad_rank, 'Quadra')
    if counts[0] == 3 and counts[1] >= 2:
        return (6, max(r for r, v in rank_count.items() if v == 3), 'Full House')
    if flush:
        return (5, ranks[0], 'Flush')
    if straight:
        return (4, straight_high, 'Sequência')
    if counts[0] == 3:
        return (3, max(r for r, v in rank_count.items() if v == 3), 'Trinca')
    if counts[0] == 2 and counts[1] == 2:
        pairs = sorted([r for r, v in rank_count.items() if v == 2], reverse=True)
        return (2, pairs[0] * 100 + pairs[1], 'Dois Pares')
    if counts[0] == 2:
        return (1, max(r for r, v in rank_count.items() if v == 2), 'Um Par')
    return (0, ranks[0], f'Carta Alta ({RANKS[ranks[0]]})')

def eval_strength(hand, community):
    cards = hand + community
    ranks = [RANK_VALUES[c['rank']] for c in cards]
    suits = [c['suit'] for c in cards]

    rank_count = {}
    for r in ranks:
        rank_count[r] = rank_count.get(r, 0) + 1
    counts = sorted(rank_count.values(), reverse=True)

    suit_count = {}
    for s in suits:
        suit_count[s] = suit_count.get(s, 0) + 1

    score = max(ranks) / 12 * 0.3

    if counts[0] == 4:
        score = 0.95
    elif counts[0] == 3 and len(counts) > 1 and counts[1] >= 2:
        score = 0.88
    elif counts[0] == 3:
        score = 0.75
    elif counts[0] == 2 and len(counts) > 1 and counts[1] == 2:
        score = max(score, 0.65)
    elif counts[0] == 2:
        score = max(score, 0.45)

    if any(v >= 5 for v in suit_count.values()):
        score = max(score, 0.85)

    return min(score, 1.0)

def print_table(state, limpar=True):
    if limpar:
        clear()
    p = state
    print("=" * 50)
    print("         TEXAS HOLD'EM POKER")
    print("=" * 50)
    print(f"  Mão #{p['hand_num']}   Blinds: $10/$20   Fase: {p['phase'].upper()}")
    print("-" * 50)
    print(f"  [CPU]  |  Fichas: ${p['cpu_chips']}  |  Aposta: ${p['cpu_bet']}")
    reveal = p['phase'] == 'showdown' or p['player_folded']
    print(f"  Cartas: {hand_str(p['cpu_hand'], hidden=not reveal)}")
    print()
    print(f"  MESA: {hand_str(p['community']) if p['community'] else '[ sem cartas ]'}")
    print(f"  POT:  ${p['pot']}")
    print()
    print(f"  [VOCE] |  Fichas: ${p['player_chips']}  |  Aposta: ${p['player_bet']}")
    print(f"  Cartas: {hand_str(p['player_hand'])}")
    print("-" * 50)
    if p.get('last_action'):
        print(f"  >> {p['last_action']}")
    print()

def get_int(prompt, min_val, max_val):
    while True:
        try:
            val = int(input(prompt))
            if min_val <= val <= max_val:
                return val
            print(f"  Digite um valor entre {min_val} e {max_val}.")
        except ValueError:
            print("  Valor inválido.")

def player_turn(state):
    to_call = state['current_bet'] - state['player_bet']
    options = []

    print("  Suas opções:")
    options.append(('fold', 'Fold'))
    if to_call <= 0:
        options.append(('check', 'Check'))
    else:
        options.append(('call', f'Call (${min(to_call, state["player_chips"])})'))
    if state['player_chips'] > to_call:
        options.append(('raise', 'Raise'))
    options.append(('allin', f'All-In (${state["player_chips"]})'))

    for i, (_, label) in enumerate(options, 1):
        print(f"  [{i}] {label}")

    choice = get_int("  Escolha: ", 1, len(options)) - 1
    action = options[choice][0]

    if action == 'fold':
        state['player_folded'] = True
        state['last_action'] = "Você deu fold."

    elif action == 'check':
        state['last_action'] = "Você fez check."

    elif action == 'call':
        amt = min(to_call, state['player_chips'])
        state['player_chips'] -= amt
        state['player_bet'] += amt
        state['pot'] += amt
        if state['player_chips'] == 0:
            state['player_allin'] = True
        state['last_action'] = f"Você pagou ${amt}."

    elif action == 'raise':
        min_raise = max(state['current_bet'] * 2, state['current_bet'] + 20) - state['player_bet']
        min_raise = max(min_raise, 1)
        max_raise = state['player_chips']
        print(f"  Raise mínimo: ${min_raise} | Máximo: ${max_raise}")
        amt = get_int("  Valor do raise: $", min_raise, max_raise)
        state['player_chips'] -= amt
        state['player_bet'] += amt
        state['pot'] += amt
        if state['player_bet'] > state['current_bet']:
            state['current_bet'] = state['player_bet']
        if state['player_chips'] == 0:
            state['player_allin'] = True
        state['last_action'] = f"Você fez raise para ${state['player_bet']}."

    elif action == 'allin':
        amt = state['player_chips']
        state['player_chips'] = 0
        state['player_bet'] += amt
        state['pot'] += amt
        if state['player_bet'] > state['current_bet']:
            state['current_bet'] = state['player_bet']
        state['player_allin'] = True
        state['last_action'] = f"Você foi all-in por ${state['player_bet']}!"

    return action

def cpu_turn(state, after_player_raise=False):
    to_call = state['current_bet'] - state['cpu_bet']
    if to_call < 0:
        to_call = 0
    strength = eval_strength(state['cpu_hand'], state['community'])

    if to_call == 0:
        if random.random() < 0.35 and strength > 0.5 and state['cpu_chips'] > 40:
            _cpu_raise(state)
        else:
            state['last_action'] = "CPU fez check."
        return 'check'

    fold_thresh = 0.5 if strength < 0.25 else (0.25 if strength < 0.45 else 0.08)
    r = random.random()

    if r < fold_thresh:
        state['cpu_folded'] = True
        state['last_action'] = "CPU deu fold."
        return 'fold'

    if r < fold_thresh + 0.35 and strength > 0.75 and to_call < state['cpu_chips'] and not after_player_raise:
        _cpu_raise(state)
        return 'raise'

    amt = min(to_call, state['cpu_chips'])
    state['cpu_chips'] -= amt
    state['cpu_bet'] += amt
    state['pot'] += amt
    if state['cpu_chips'] == 0:
        state['cpu_allin'] = True
    state['last_action'] = f"CPU pagou ${amt}."
    return 'call'

def _cpu_raise(state):
    min_raise = max(state['current_bet'] * 2, state['current_bet'] + 20) - state['cpu_bet']
    min_raise = max(min_raise, 1)
    amt = min(min_raise + random.randint(0, 60), state['cpu_chips'])
    state['cpu_chips'] -= amt
    state['cpu_bet'] += amt
    state['pot'] += amt
    if state['cpu_bet'] > state['current_bet']:
        state['current_bet'] = state['cpu_bet']
    if state['cpu_chips'] == 0:
        state['cpu_allin'] = True
    state['last_action'] = f"CPU fez raise para ${state['cpu_bet']}!"

def post_blind(state, who, amt):
    amt = min(amt, state[f'{who}_chips'])
    state[f'{who}_chips'] -= amt
    state[f'{who}_bet'] += amt
    state['pot'] += amt

def play_phase(state, deck, phase_name):
    state['phase'] = phase_name
    state['player_bet'] = 0
    state['cpu_bet'] = 0
    state['current_bet'] = 0

    if phase_name == 'flop':
        state['community'] += [deck.pop(), deck.pop(), deck.pop()]
    elif phase_name in ('turn', 'river'):
        state['community'].append(deck.pop())

    if state['player_folded'] or state['cpu_folded']:
        return

    both_allin = state['player_allin'] and state['cpu_allin']
    if both_allin:
        print_table(state, limpar=False)
        input("  [Enter para continuar]")
        return

    dealer = state['dealer']

    if dealer == 'cpu':
        print_table(state, limpar=False)
        act = cpu_turn(state)
        print(f"  >> {state['last_action']}")
        if state['cpu_folded']:
            return
        if act in ('check', 'call'):
            if not state['player_allin']:
                input("  [Enter para sua vez] ")
                print_table(state)
                player_turn(state)
        elif act == 'raise':
            input("  CPU fez raise! [Enter para responder] ")
            print_table(state)
            pa = player_turn(state)
            if pa == 'raise' and not state['cpu_allin']:
                cpu_turn(state, after_player_raise=True)
                print(f"  >> {state['last_action']}")
    else:
        if not state['player_allin']:
            input("  [Enter para sua vez] ")
            print_table(state)
            pa = player_turn(state)
            if state['player_folded']:
                return
            if pa == 'raise':
                cpu_turn(state, after_player_raise=True)
                print(f"  >> {state['last_action']}")
                if state['cpu_folded']:
                    return
                if not state['cpu_allin']:
                    input("  CPU relançou! [Enter para responder] ")
                    print_table(state)
                    player_turn(state)
            else:
                cpu_turn(state)
                print(f"  >> {state['last_action']}")
        else:
            cpu_turn(state)
            print(f"  >> {state['last_action']}")

    print_table(state, limpar=False)

def showdown(state):
    state['phase'] = 'showdown'
    print_table(state, limpar=False)
    ph = rank_hand(state['player_hand'], state['community'])
    ch = rank_hand(state['cpu_hand'], state['community'])
    print(f"  Sua mão:  {ph[2]}")
    print(f"  CPU mão:  {ch[2]}")
    print()
    if ph[0] > ch[0] or (ph[0] == ch[0] and ph[1] >= ch[1]):
        if ph[0] == ch[0] and ph[1] == ch[1]:
            half = state['pot'] // 2
            state['player_chips'] += half
            state['cpu_chips'] += half
            state['pot'] = 0
            print("  EMPATE! Pot dividido.")
        else:
            state['player_chips'] += state['pot']
            state['pot'] = 0
            print("  VOCE VENCEU!")
    else:
        state['cpu_chips'] += state['pot']
        state['pot'] = 0
        print("  CPU VENCEU!")
    print()

def award_pot(state, winner):
    if winner == 'player':
        state['player_chips'] += state['pot']
        print("  Voce ganhou o pot (CPU foldou)!")
    else:
        state['cpu_chips'] += state['pot']
        print("  CPU ganhou o pot (voce foldou)!")
    state['pot'] = 0

def play_hand(player_chips, cpu_chips, hand_num, dealer):
    deck = shuffle(build_deck())
    state = {
        'hand_num': hand_num,
        'phase': 'preflop',
        'player_hand': [deck.pop(), deck.pop()],
        'cpu_hand': [deck.pop(), deck.pop()],
        'community': [],
        'pot': 0,
        'player_chips': player_chips,
        'cpu_chips': cpu_chips,
        'player_bet': 0,
        'cpu_bet': 0,
        'current_bet': 0,
        'player_folded': False,
        'cpu_folded': False,
        'player_allin': False,
        'cpu_allin': False,
        'dealer': dealer,
        'last_action': '',
    }

    sb = dealer
    bb = 'cpu' if dealer == 'player' else 'player'
    post_blind(state, sb, 10)
    post_blind(state, bb, 20)
    state['current_bet'] = 20

    state['phase'] = 'preflop'
    print_table(state)
    print(f"  Dealer: {'Você' if dealer == 'player' else 'CPU'}  |  SB: {'Você' if sb == 'player' else 'CPU'} ($10)  BB: {'Você' if bb == 'player' else 'CPU'} ($20)")

    if dealer == 'player':
        input("  [Enter para sua vez no pré-flop] ")
        print_table(state)
        pa = player_turn(state)
        if not state['player_folded']:
            if pa == 'raise':
                cpu_turn(state, after_player_raise=True)
                print(f"  >> {state['last_action']}")
            else:
                cpu_turn(state)
                print(f"  >> {state['last_action']}")
    else:
        print_table(state, limpar=False)
        input("  [Enter - CPU age no pré-flop] ")
        act = cpu_turn(state)
        print(f"  >> {state['last_action']}")
        if not state['cpu_folded']:
            if act == 'raise':
                input("  CPU fez raise! [Enter para responder] ")
                print_table(state)
                player_turn(state)
            else:
                input("  [Enter para sua vez] ")
                print_table(state)
                player_turn(state)

    print_table(state, limpar=False)

    if state['player_folded']:
        award_pot(state, 'cpu')
        return state['player_chips'], state['cpu_chips']
    if state['cpu_folded']:
        award_pot(state, 'player')
        return state['player_chips'], state['cpu_chips']

    for phase in ['flop', 'turn', 'river']:
        input(f"  [Enter para o {phase.upper()}] ")
        play_phase(state, deck, phase)
        if state['player_folded']:
            award_pot(state, 'cpu')
            return state['player_chips'], state['cpu_chips']
        if state['cpu_folded']:
            award_pot(state, 'player')
            return state['player_chips'], state['cpu_chips']

    input("  [Enter para o SHOWDOWN] ")
    showdown(state)
    return state['player_chips'], state['cpu_chips']

def main():
    clear()
    print("=" * 50)
    print("      TEXAS HOLD'EM POKER")
    print("      Jogador vs CPU")
    print("=" * 50)
    print("  Cada jogador começa com $1000.")
    print("  Blinds fixos: $10 (SB) / $20 (BB).")
    print("  Vence quem falir o oponente!")
    print()
    input("  [Enter para começar] ")

    player_chips = 1000
    cpu_chips = 1000
    hand_num = 0
    dealer = 'player'

    while player_chips > 0 and cpu_chips > 0:
        hand_num += 1
        player_chips, cpu_chips = play_hand(player_chips, cpu_chips, hand_num, dealer)
        dealer = 'cpu' if dealer == 'player' else 'player'

        print(f"\n  Fichas - Você: ${player_chips} | CPU: ${cpu_chips}")
        if player_chips <= 0:
            print("\n  Voce perdeu tudo! CPU venceu o jogo.")
            break
        if cpu_chips <= 0:
            print("\n  CPU faliu! Voce dominou a mesa!")
            break

        resp = input("\n  Jogar outra mão? (s/n): ").strip().lower()
        if resp != 's':
            print("\n  Obrigado por jogar!")
            break

    print()
    sys.exit(0)

if __name__ == '__main__':
    main()
