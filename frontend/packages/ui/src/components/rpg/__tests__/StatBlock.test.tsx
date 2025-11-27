import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatBlock } from '../StatBlock';

describe('StatBlock', () => {
  it('should render stat block with correct values', () => {
    render(<StatBlock label="STR" value={16} />);
    
    expect(screen.getByText('STR')).toBeInTheDocument();
    expect(screen.getByText('16')).toBeInTheDocument();
    expect(screen.getByText('+3')).toBeInTheDocument();
  });

  it('should calculate modifier correctly', () => {
    render(<StatBlock label="DEX" value={8} />);
    expect(screen.getByText('-1')).toBeInTheDocument();
  });

  it('should use provided modifier if given', () => {
    render(<StatBlock label="CON" value={10} modifier={5} />);
    expect(screen.getByText('+5')).toBeInTheDocument();
  });
});



