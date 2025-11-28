import { Monster } from './types';

export const creatures: Monster[] = [
    {
        id: 'monster-1',
        name: 'Goblin',
        type: 'Humanoid (Goblinoid)',
        size: 'Small',
        ac: 15,
        hp: 7,
        stats: {
            str: 8,
            dex: 14,
            con: 10,
            int: 10,
            wis: 8,
            cha: 8
        },
        actions: [
            {
                name: 'Scimitar',
                desc: 'Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) slashing damage.',
                attack_bonus: 4,
                damage_dice: '1d6+2'
            },
            {
                name: 'Shortbow',
                desc: 'Ranged Weapon Attack: +4 to hit, range 80/320 ft., one target. Hit: 5 (1d6 + 2) piercing damage.',
                attack_bonus: 4,
                damage_dice: '1d6+2'
            }
        ]
    },
    {
        id: 'monster-2',
        name: 'Orc',
        type: 'Humanoid (Orc)',
        size: 'Medium',
        ac: 13,
        hp: 15,
        stats: {
            str: 16,
            dex: 12,
            con: 16,
            int: 7,
            wis: 11,
            cha: 10
        },
        actions: [
            {
                name: 'Greataxe',
                desc: 'Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 9 (1d12 + 3) slashing damage.',
                attack_bonus: 5,
                damage_dice: '1d12+3'
            },
            {
                name: 'Javelin',
                desc: 'Melee or Ranged Weapon Attack: +5 to hit, reach 5 ft. or range 30/120 ft., one target. Hit: 6 (1d6 + 3) piercing damage.',
                attack_bonus: 5,
                damage_dice: '1d6+3'
            }
        ]
    }
];
