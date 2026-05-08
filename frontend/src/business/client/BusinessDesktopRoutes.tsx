import { type RouteObject } from 'react-router-dom';

import { BiddingWorkbench } from '@/features/Bidding';

export const BusinessDesktopRoutesWithMainLayout: RouteObject[] = [
  {
    path: 'bid',
    element: <BiddingWorkbench />,
  },
];
export const BusinessDesktopRoutesWithSettingsLayout: RouteObject[] = [];
export const BusinessDesktopRoutesWithoutMainLayout: RouteObject[] = [];
