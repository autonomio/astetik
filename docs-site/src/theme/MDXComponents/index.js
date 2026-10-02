import React, {useEffect, useRef, useState} from 'react';
import OriginalMDXComponents from '@theme-original/MDXComponents';

function ScrollableTable(props) {
  const element = useRef(null);
  const [scrollable, setScrollable] = useState(false);
  useEffect(() => {
    let active = true;
    const measure = () => {
      if (active && element.current) {
        setScrollable(element.current.scrollWidth > element.current.clientWidth + 1);
      }
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element.current);
    document.fonts.ready.then(measure);
    return () => {
      active = false;
      observer.disconnect();
    };
  }, []);
  return <table {...props} ref={element} tabIndex={scrollable ? 0 : props.tabIndex} />;
}

export default {
  ...OriginalMDXComponents,
  table: ScrollableTable,
};
