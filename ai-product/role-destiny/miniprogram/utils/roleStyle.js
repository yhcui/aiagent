/**
 * 宫廷角色视觉档案
 * 每个角色：徽记 emoji + 袍色渐变（CSS）+ 渐变色柱（Canvas）+ 核心色 + 浅晕底
 * 以角色 code 为键（A-H），供首页/结果页/记录页/海报共用
 */
const ROLE_STYLES = {
  A: {
    name: '宠儿',
    emblem: '🌸',
    grad: 'linear-gradient(135deg, #FFC9D8 0%, #FF9DB8 100%)',
    hexes: ['#FFC9D8', '#FF9DB8'],
    core: '#E86F96',
    coreRGB: '232,111,150',
    tint: '#FFF0F5',
  },
  B: {
    name: '谋士',
    emblem: '📜',
    grad: 'linear-gradient(135deg, #BCD2E4 0%, #6C8FB0 100%)',
    hexes: ['#BCD2E4', '#6C8FB0'],
    core: '#4A6B8A',
    coreRGB: '74,107,138',
    tint: '#F0F5FA',
  },
  C: {
    name: '女官',
    emblem: '⚖️',
    grad: 'linear-gradient(135deg, #F2DFAE 0%, #D4AE5C 100%)',
    hexes: ['#F2DFAE', '#D4AE5C'],
    core: '#B08A37',
    coreRGB: '176,138,55',
    tint: '#FBF5E5',
  },
  D: {
    name: '将星',
    emblem: '⚔️',
    grad: 'linear-gradient(135deg, #EBB3AC 0%, #C25350 100%)',
    hexes: ['#EBB3AC', '#C25350'],
    core: '#A84240',
    coreRGB: '168,66,64',
    tint: '#FBEEEC',
  },
  E: {
    name: '医女',
    emblem: '🌿',
    grad: 'linear-gradient(135deg, #B9E3D0 0%, #69B294 100%)',
    hexes: ['#B9E3D0', '#69B294'],
    core: '#4E9779',
    coreRGB: '78,151,121',
    tint: '#EFF8F3',
  },
  F: {
    name: '乐师',
    emblem: '🎵',
    grad: 'linear-gradient(135deg, #D6C2E8 0%, #9979B8 100%)',
    hexes: ['#D6C2E8', '#9979B8'],
    core: '#7C5FA3',
    coreRGB: '124,95,163',
    tint: '#F5F0FA',
  },
  G: {
    name: '画师',
    emblem: '🎨',
    grad: 'linear-gradient(135deg, #B2DAE6 0%, #58A3C0 100%)',
    hexes: ['#B2DAE6', '#58A3C0'],
    core: '#3F86A3',
    coreRGB: '63,134,163',
    tint: '#EFF7FA',
  },
  H: {
    name: '绣娘',
    emblem: '🧵',
    grad: 'linear-gradient(135deg, #F2C3CE 0%, #DE6B84 100%)',
    hexes: ['#F2C3CE', '#DE6B84'],
    core: '#C25570',
    coreRGB: '194,85,112',
    tint: '#FBEEF2',
  },
};

/**
 * 获取角色视觉样式（未知 code 回退到默认粉系）
 */
function getRoleStyle(code) {
  return ROLE_STYLES[code] || {
    name: '',
    emblem: '✨',
    grad: 'linear-gradient(135deg, #FFC9D8 0%, #FF9DB8 100%)',
    hexes: ['#FFC9D8', '#FF9DB8'],
    core: '#FF6B9D',
    coreRGB: '255,107,157',
    tint: '#FFF0F3',
  };
}

/**
 * 稀有度玉档（依据 rarity 值）
 * 稀世（金） < 0.10 ≤ 珍品（紫） < 0.16 ≤ 寻常（黛）
 */
function rarityLabel(rarity) {
  const r = Number(rarity) || 0.15;
  if (r < 0.10) return { label: '稀世', cls: 'seal-gold' };
  if (r < 0.16) return { label: '珍品', cls: 'seal-plum' };
  return { label: '寻常', cls: 'seal-teal' };
}

/**
 * 首页月门展示的徽记队列（视觉搭配）
 */
const GATE_EMBLEMS = ['A', 'C', 'E'];

module.exports = {
  ROLE_STYLES,
  GATE_EMBLEMS,
  getRoleStyle,
  rarityLabel,
};