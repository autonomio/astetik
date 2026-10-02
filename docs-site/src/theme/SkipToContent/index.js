import React from 'react';
import {SkipToContentFallbackId} from '@docusaurus/theme-common';
import OriginalSkipToContent from '@theme-original/SkipToContent';

export default function SkipToContent() {
  const focusContent = (event) => {
    if (!event.target.closest(`a[href="#${SkipToContentFallbackId}"]`)) return;
    const target = document.querySelector('main') ?? document.getElementById(SkipToContentFallbackId);
    if (!target) return;
    event.preventDefault();
    event.stopPropagation();
    // Keep the target programmatically focusable: Chromium blurs it when the
    // upstream handler immediately removes tabindex after focus().
    target.setAttribute('tabindex', '-1');
    target.focus();
  };
  return <div onClickCapture={focusContent}><OriginalSkipToContent /></div>;
}
