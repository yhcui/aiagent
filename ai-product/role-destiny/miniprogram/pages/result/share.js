/**
 * 分享海报页 - 命格御画（Canvas 2D 绘制）
 */
const app = getApp();
const quizService = require('../../services/quizService');
const { getRoleStyle } = require('../../utils/roleStyle');

const W = 560;
const H = 1000;

Page({
  data: {
    resultId: null,
    statusBarH: 20,
    posterReady: false,
    drawError: '',
    posterTemp: '',
    roleName: '神秘命格',
  },

  posterData: null,

  onLoad(options) {
    const resultId = parseInt(options.resultId);
    if (!resultId) {
      wx.showToast({ title: '参数错误', icon: 'none' });
      setTimeout(() => wx.navigateBack(), 800);
      return;
    }

    const sysInfo = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    this.setData({ resultId, statusBarH: sysInfo.statusBarHeight || 20 });
    this.prepareAndDraw();
  },

  async prepareAndDraw() {
    try {
      const result = await quizService.getResult(this.data.resultId, app.globalData.openid);
      const roleStyle = getRoleStyle(result.role.code);
      const nickname = (app.globalData.userInfo && app.globalData.userInfo.nickname) || '神秘小主';

      this.posterData = {
        roleName: result.role.name,
        emblem: roleStyle.emblem,
        hexes: roleStyle.hexes,
        desc: result.role.description || '',
        match: Math.round(result.match_score),
        nickname,
      };

      this.setData({ roleName: result.role.name, drawError: '' });

      // 先让画布上屏，渲染完成后再绘制
      this.setData({ posterReady: true }, () => {
        this.paintPoster(this.posterData);
      });
    } catch (err) {
      console.error('Poster prepare failed:', err);
      this.setData({
        posterReady: false,
        drawError: err && err.message ? err.message : '取命格数据失败',
      });
    }
  },

  redraw() {
    this.setData({ drawError: '' });
    if (this.posterData) {
      this.setData({ posterReady: true }, () => {
        this.paintPoster(this.posterData);
      });
    } else {
      this.prepareAndDraw();
    }
  },

  /**
   * 分段文本换行（按字符测量）
   */
  wrapText(ctx, text, maxWidth, maxLines) {
    const lines = [];
    let line = '';
    for (const ch of text) {
      if (ctx.measureText(line + ch).width > maxWidth && line) {
        lines.push(line);
        line = ch;
        if (lines.length === maxLines) break;
      } else {
        line += ch;
      }
    }
    if (lines.length < maxLines && line) lines.push(line);
    if (lines.length >= maxLines && lines[maxLines - 1] && lines[maxLines - 1].length > 4) {
      lines[maxLines - 1] = lines[maxLines - 1].slice(0, -1) + '…';
    }
    return lines;
  },

  /**
   * 查询画布并绘制（节点未就绪时自动重试）
   */
  paintPoster(p, attempt = 0) {
    const query = wx.createSelectorQuery();
    query
      .select('#posterCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        const canvas = res && res[0] && res[0].node;

        if (!canvas) {
          // 画布节点尚未渲染完成，稍后重试
          if (attempt < 4) {
            setTimeout(() => this.paintPoster(p, attempt + 1), 300);
            return;
          }
          this.setData({
            posterReady: false,
            drawError: '画布初始化失败，请再画一次',
          });
          return;
        }

        try {
          const ctx = canvas.getContext('2d');
          const dpr = wx.getWindowInfo().pixelRatio || 2;

          canvas.width = W * dpr;
          canvas.height = H * dpr;
          ctx.scale(dpr, dpr);

          this.paint(ctx, p);

          this.exportPoster(canvas);
        } catch (err) {
          console.error('Draw poster failed:', err);
          this.setData({
            posterReady: false,
            drawError: '绘制失败，请再画一次',
          });
        }
      });
  },

  paint(ctx, p) {
    const cx = W / 2;
    const name = p.roleName || '神秘';
    const [c1, c2] = p.hexes;

    // 袍色渐变底
    const bg = ctx.createLinearGradient(0, 0, W, H);
    bg.addColorStop(0, c1);
    bg.addColorStop(1, c2);
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    // 晕光
    const glow = ctx.createRadialGradient(cx, 140, 20, cx, 140, 420);
    glow.addColorStop(0, 'rgba(255,255,255,0.55)');
    glow.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, W, 480);

    // 金角
    ctx.strokeStyle = 'rgba(245,233,206,0.6)';
    ctx.lineWidth = 2;
    const corner = (x, y, dx, dy) => {
      ctx.beginPath();
      ctx.moveTo(x + dx, y);
      ctx.lineTo(x, y);
      ctx.lineTo(x, y + dy);
      ctx.stroke();
    };
    corner(28, 28, 34, 34);
    corner(W - 28, 28, -34, 34);
    corner(28, H - 28, 34, -34);
    corner(W - 28, H - 28, -34, -34);

    // 品牌行
    ctx.fillStyle = 'rgba(255,255,255,0.8)';
    ctx.font = '22px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('角 色 测 算 · 宫 闱 命 格', cx, 76);

    // 金印
    const seal = ctx.createLinearGradient(cx - 46, 112, cx + 46, 204);
    seal.addColorStop(0, '#E8C878');
    seal.addColorStop(1, '#C9A24B');
    const rrect = (x, y, w, h, r) => {
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    };
    ctx.fillStyle = seal;
    rrect(cx - 46, 112, 92, 92, 20);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 56px serif';
    ctx.fillText('命', cx, 180);

    // 徽记
    ctx.font = '96px sans-serif';
    ctx.fillText(p.emblem, cx, 290);

    // 名号
    ctx.save();
    ctx.shadowColor = 'rgba(0,0,0,0.25)';
    ctx.shadowBlur = 14;
    ctx.shadowOffsetY = 4;
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 64px serif';
    ctx.fillText(name, cx, 384);
    ctx.restore();

    // 稀有度签
    const sealLabel = p.match >= 92 ? '稀 世 命 格' : '宫 廷 命 格';
    ctx.font = '22px sans-serif';
    const sealW = ctx.measureText(sealLabel).width + 44;
    ctx.fillStyle = 'rgba(255,255,255,0.30)';
    rrect(cx - sealW / 2, 404, sealW, 42, 21);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(sealLabel, cx, 433);

    // 判词/描述
    const lines = this.wrapText(ctx, p.desc, 470, 3);
    ctx.font = '24px sans-serif';
    ctx.fillStyle = 'rgba(255,255,255,0.92)';
    lines.forEach((ln, i) => {
      ctx.fillText(ln, cx, 492 + i * 40);
    });

    // 装饰线
    ctx.strokeStyle = 'rgba(255,255,255,0.35)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(110, 576);
    ctx.lineTo(cx - 30, 576);
    ctx.moveTo(cx + 30, 576);
    ctx.lineTo(W - 110, 576);
    ctx.stroke();
    ctx.fillStyle = '#F5E9CE';
    ctx.font = '24px sans-serif';
    ctx.fillText('✦', cx, 582);

    // 契合度
    ctx.fillStyle = 'rgba(255,255,255,0.78)';
    ctx.font = '24px sans-serif';
    ctx.fillText('命 格 契 合 度', cx, 620);

    ctx.save();
    ctx.shadowColor = 'rgba(0,0,0,0.2)';
    ctx.shadowBlur = 10;
    ctx.shadowOffsetY = 3;
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 86px serif';
    ctx.fillText(String(p.match), cx, 712);
    ctx.restore();
    ctx.font = '34px serif';
    ctx.fillText('%', cx + 56, 696);

    // 丝带
    const trackX = 110;
    const trackW = W - 220;
    ctx.fillStyle = 'rgba(255,255,255,0.28)';
    rrect(trackX, 740, trackW, 14, 7);
    ctx.fill();
    const fillW = Math.max(14, (trackW * p.match) / 100);
    const silk = ctx.createLinearGradient(trackX, 0, trackX + fillW, 0);
    silk.addColorStop(0, '#FFFFFF');
    silk.addColorStop(1, '#F5E9CE');
    ctx.fillStyle = silk;
    rrect(trackX, 740, fillW, 14, 7);
    ctx.fill();

    // 昵称
    ctx.fillStyle = 'rgba(255,255,255,0.82)';
    ctx.font = '22px sans-serif';
    ctx.fillText(`— 「${p.nickname}」在此揭晓命格 —`, cx, 792);

    // 底部白卡 + 红印
    const card = { x: cx - 108, y: 812, w: 216, h: 184, r: 22 };
    ctx.fillStyle = 'rgba(255,255,255,0.96)';
    rrect(card.x, card.y, card.w, card.h, card.r);
    ctx.fill();

    // 红印（角色名双字）
    ctx.fillStyle = '#B03A3A';
    rrect(cx - 56, card.y + 18, 112, 112, 14);
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.9)';
    ctx.lineWidth = 3;
    ctx.strokeRect(cx - 48, card.y + 26, 96, 96);

    const chars = name.split('').slice(0, 2);
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 44px serif';
    if (chars.length === 2) {
      ctx.fillText(chars[0], cx, card.y + 62);
      ctx.fillText(chars[1], cx, card.y + 116);
    } else {
      ctx.fillText(name, cx, card.y + 84);
    }

    ctx.fillStyle = '#8A7B82';
    ctx.font = '20px sans-serif';
    ctx.fillText('角色测算 · 测测你的宫闱命格', cx, card.y + card.h - 14);
  },

  /**
   * 导出临时文件（用于分享图）
   */
  exportPoster(canvas) {
    wx.canvasToTempFilePath({
      canvas,
      success: (res) => {
        this.setData({ posterTemp: res.tempFilePath });
      },
      fail: (err) => {
        console.error('Export poster failed:', err);
      },
    });
  },

  /**
   * 保存到相册
   */
  savePoster() {
    if (!this.data.posterReady) return;

    app.showLoading('保存中…');

    const doSave = (filePath) => {
      wx.saveImageToPhotosAlbum({
        filePath,
        success: () => {
          app.hideLoading();
          app.showSuccess('已存入相册');
        },
        fail: (err) => {
          app.hideLoading();
          if (err.errMsg && err.errMsg.includes('auth deny')) {
            wx.showModal({
              title: '需要相册权限',
              content: '请允许保存图片到相册，才能收藏你的命格御画',
              confirmText: '去开启',
              success: (res) => {
                if (res.confirm) wx.openSetting();
              },
            });
          } else {
            app.handleError(err);
          }
        },
      });
    };

    if (this.data.posterTemp) {
      doSave(this.data.posterTemp);
    } else {
      wx.createSelectorQuery()
        .select('#posterCanvas')
        .fields({ node: true })
        .exec((res) => {
          if (res[0] && res[0].node) {
            wx.canvasToTempFilePath({
              canvas: res[0].node,
              success: (r) => doSave(r.tempFilePath),
              fail: () => app.handleError(new Error('导出失败，请再试一次')),
            });
          }
        });
    }
  },

  close() {
    wx.navigateBack();
  },

  onShareAppMessage() {
    return {
      title: `我在「角色测算」测出了「${this.data.roleName}」，你也来测测！`,
      path: `/pages/index/index`,
      imageUrl: this.data.posterTemp || '',
    };
  },
});